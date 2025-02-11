# PlumberAPI.R - Functions to be hosted by plumber to allow a Python parent
# process to control an R child process.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

library(jsonlite)
library(plumber)

###############################################################################
# Helper functions
###############################################################################

#' Execute expr and, if it fails, attach character vector of the call stack tree to the error.
#'
#' @param expr Expression to execute.
#' @return The result of the evaluation of expr.
#'
captureTraceback <- function(expr) {
  withCallingHandlers(
    expr,
    error = function(e) {
      if (is.null(attr(e, "cst", exact = TRUE))) {
        cst <- rlang::trace_back()
        attr(e, "cst") <- capture.output(print(cst, simplify = "none"))
        cat("API_CALL_DONE\n"); message("API_CALL_DONE")
        signalCondition(e)
      }
    }
  )
}

#' Returns a character vector representing the value of an object, suitable for logging
#'
#' Each element of the returned vector is one line to be logged. If the size
#' used by the object is more than 1024 bytes, a single line will be returned
#' giving the object's size, class, and possibly dimensions. If the object is
#' less than or equal to 1024 bytes, additional lines may be returned,
#' depending the value of the object. All lines will be terminated by a
#' newline, even if only one line is returned.
#'
#' @param obj Object to be logged.
#' @return Character vector of lines to be logged.
#'
getValueForLogging <- function(obj) {
  if (any(class(obj) %in% c("numeric", "integer", "complex", "logical", "character")) && length(obj) == 0) {
    return(paste0(capture.output(print(obj)), "\n"))
  }
  if (any(class(obj) %in% c("numeric", "integer", "complex", "logical")) && length(obj) == 1 ||
      any(class(obj) == "character") && length(obj) == 1 && object.size(obj) <= 1024) {
    s <- capture.output(print(obj))
    return(paste0(substr(s, 5, nchar(s)), "\n"))
  }
  if (any(class(obj) %in% c("data.frame", "tibble"))) {
    line1 <- sprintf("%s with %i rows, %i columns", paste0(class(obj), collapse="|"), nrow(obj), ncol(obj))
  } else {
    line1 <- sprintf("length %i %s", length(obj), paste0(class(obj), collapse="|"))
  }
  if (object.size(obj) > 1024) {
    return(paste0(line1, "\n"))
  }
  lines <- capture.output(print(obj))
  if (nchar(lines[length(lines)]) == 0) {
    lines <- lines[1:length(lines)-1]
  }
  return(c(paste0(line1, ":\n"), sprintf("  %s\n", lines)))
}

#' A serializer that emits JSON customized for parsing by our Python caller
#'
#' This serializer emits doubles at full (17-digit) precision and renders the
#' special values NaN, Inf, and -Inf as "NaN", "Infinity", and "-Infinity"
#' (without the quotes), which the Python json module will parse as those
#' special values. This serializer also emits JSON null for R NULL and NA,
#' renders POSIXt values in "mongo" format, automatically unclasses objects
#' (via force=TRUE), and automatically unboxes length 1 vectors.
#'
#' NOTE: For digits, the plumber ' documentation says to use NA for full
#' precision, but at the time of this writing, jsonlite::toJSON treated NA as
#' 15 digits, which is not enough for full 64-bit float precision. See: 
#' https://github.com/jeroen/jsonlite/commit/120cca8df83f6f6e6ce26610b113c15e881a95de

serializer_unboxed_json_for_python <- function(auto_unbox=TRUE, na="string", null="null", digits=17, POSIXt="mongo", force=TRUE, ..., type="application/json") {
  serializer_content_type(type, function(val) {
    val <- jsonlite::toJSON(val, auto_unbox=auto_unbox, na=na, null=null, digits=digits, POSIXt=POSIXt, force=force, ...)
    val <- gsub('(?<!\\\\)"NaN"', 'NaN', val, perl=TRUE)
    val <- gsub('(?<!\\\\)"-Inf"', '-Infinity', val, perl=TRUE)
    val <- gsub('(?<!\\\\)"Inf"', 'Infinity', val, perl=TRUE)
    val <- gsub('(?<!\\\\)"NA"', 'null', val, perl=TRUE)
    val
  })
}

###############################################################################
# API functions exposed through plumber
###############################################################################

# Define an environment to be used to hold objects for the HTTP client. These
# objects are created and manipulated by the functions that follow.

clientEnv <- new.env()

#* Return the string that was provided.
#* @get /echo
#* @param msg The string to return.
function(msg = "") {
  cat("API_CALL_DONE\n"); message("API_CALL_DONE")
  msg
}

#* Log an informational message. Calls cat() to write it to stdout.
#* @post /log-info
#* @param msg The string to log.
function(msg = "") {
  if (!endsWith(msg, "\n")) {
    msg <- paste0(msg, "\n")
  }
  cat(msg)
  cat("API_CALL_DONE\n"); message("API_CALL_DONE")
  return()
}

#* Log a warning message. Calls message() to write it to stderr.
#* @post /log-warning
#* @param msg The string to log.
function(msg = "") {
  message(msg)   # message() automatically adds a newline, so we don't need to
  cat("API_CALL_DONE\n"); message("API_CALL_DONE")
  return()
}

#* Shut down the R child process.
#* @post /shutdown
function() {
  cat("API_CALL_DONE\n"); message("API_CALL_DONE")
  quit(save = "no", status = 0)
}

#* Returns a list of the names of the variables that have been defined.
#* @post /list
function() {
  captureTraceback({
    value <- ls(envir=clientEnv)

    lines <- getValueForLogging(value)
    lines[1] <- paste0("LIST: ", lines[1])
    for (line in lines) {
      cat("DEBUG:", line)
    }

    cat("API_CALL_DONE\n"); message("API_CALL_DONE")
    value
  })
}

#* Sets a variable to a value.
#* @put /set
#* @param name The name of the variable to set.
#* @param value The value for the variable.
#* @parser multi
#* @parser json
#* @parser feather
#* @parser parquet
function(name, value) {
  captureTraceback({

    # Validate the parameter values.
    
    if (missing(name) || class(name) != "character" || length(name) != 1 || nchar(trimws(name)) <= 0) {
      stop("The \"name\" parameter is required. It must be a single string with a length > 0.", call.=FALSE)
    }
    name <- trimws(name)

    if (missing(value)) {
      stop("The \"value\" parameter is required.")
    }

    # To work around apparent JSON deserialization bugs in the plumber or
    # jsonlite packages , check whether value is a list that contains an item
    # named RWorkerProcess_IsAtomicDatetime. If so, extract the atomic
    # POSIXct from within it. Similarly, if value is a list that contains an
    # item named RWorkerProcess_IsDatetimeList, just remove that item and
    # proceed with the list. See the comments in _SerializeToJSON
    # in _RWorkerProcess.py for more information about these kludges.

    if (typeof(value) == "list" && "RWorkerProcess_IsAtomicDatetime" %in% names(value)) {
      value <- value$value
    } else if (typeof(value) == "list" && "RWorkerProcess_IsDatetimeList" %in% names(value)) {
      value$RWorkerProcess_IsDatetimeList <- NULL
    }

    # Log a debug message.

    lines <- getValueForLogging(value)
    lines[1] <- paste0("SET: ", name, " <- ", lines[1])
    for (line in lines) {
      cat("DEBUG:", line)
    }

    # Assign the variable in clientEnv.

    assign(name, value, envir=clientEnv)
    cat("API_CALL_DONE\n"); message("API_CALL_DONE")
    return()
  })
}

serializers <- list(
  json=serializer_unboxed_json_for_python(), 
  feather=serializer_feather()
)

#* Returns the value of a variable.
#* @post /get
#* @param name The name of the variable to get.
function(name, res) {
  captureTraceback({

    # Validate the parameter values.
    
    if (missing(name) || class(name) != "character" || length(name) != 1 || nchar(trimws(name)) <= 0) {
      stop("The \"name\" parameter is required. It must be a single string with a length > 0.", call.=FALSE)
    }
    name <- trimws(name)

    # Get the value.

    if (!exists(name, envir=clientEnv)) {
      stop(sprintf("Object '%s' not found", name), call.=FALSE)
    }
    value <- get(name, envir=clientEnv)

    # Log a debug message.

    lines <- getValueForLogging(value)
    lines[1] <- paste0("GET: ", name, " == ", lines[1])
    for (line in lines) {
      cat("DEBUG:", line)
    }

    # If the value is a dataframe or a tibble, set the serializer to feather.
    # Otherwise use unboxed JSON. Then return the value.

    if ("data.frame" %in% class(value) || "tibble" %in% class(value)) {
      res$serializer <- serializers$feather
    } else {
       res$serializer <- serializers$json
    }

    cat("API_CALL_DONE\n"); message("API_CALL_DONE")
    value
  })
}

#* Deletes a variable.
#* @delete /delete
#* @param name The name of the variable to delete.
function(name) {
  captureTraceback({

    # Validate the parameter values.
    
    if (missing(name) || class(name) != "character" || length(name) != 1 || nchar(trimws(name)) <= 0) {
      stop("The \"name\" parameter is required. It must be a single string with a length > 0.", call.=FALSE)
    }
    name <- trimws(name)

    if (!exists(name, envir=clientEnv)) {
      stop(sprintf("Object '%s' not found", name), call.=FALSE)
    }

    # Delete the variable from clientEnv.

    cat(sprintf("DEBUG: DELETE: %s\n", name))
    rm(list=name, envir=clientEnv)
    cat("API_CALL_DONE\n"); message("API_CALL_DONE")
    return()
  })
}

#* Evaluates an expression and returns the result.
#* @post /eval
#* @param expr The expression to evaluate.
function(expr, res) {
  captureTraceback({

    # Validate the parameter values.
    
    if (missing(expr) || class(expr) != "character" || length(expr) != 1 || nchar(trimws(expr)) <= 0) {
      stop("The \"expr\" parameter is required. It must be a single string with a length > 0.", call.=FALSE)
    }
    expr <- trimws(expr)

    # Write the expression to a debug message.

    lines <- strsplit(expr, "\n")[[1]]
    cat("DEBUG: EVAL: ", lines[1], "\n", sep="")
    if (length(lines) > 1) {
      for (line in lines[2:length(lines)]) {
        cat("DEBUG:       ", line, "\n", sep="")
      }
    }

    # Evaluate the expression in clientEnv and log the result.

    parsedExpr <- parse(text=expr, encoding="UTF-8")
    value <- eval(parsedExpr, envir=clientEnv, enclos=baseenv())

    lines <- getValueForLogging(value)
    cat("DEBUG: RESULT: ", lines[1], sep="")
    if (length(lines) > 1) {
      for (line in lines[2:length(lines)]) {
        cat("DEBUG:         ", line, sep="")
      }
    }

    # If the value is a dataframe or a tibble, set the serializer to feather.
    # Otherwise use unboxed JSON. Then return the value.

    if ("data.frame" %in% class(value) || "tibble" %in% class(value)) {
      res$serializer <- serializers$feather
    } else {
       res$serializer <- serializers$json
    }

    cat("API_CALL_DONE\n"); message("API_CALL_DONE")
    value
  })
}
