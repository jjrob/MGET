# RunPlumber.R - Script that runs plumber on a specified port and R file.
#
# Copyright (C) 2024 Jason J. Roberts
#
# This file is part of Marine Geospatial Ecology Tools (MGET) and is released
# under the terms of the 3-Clause BSD License. See the LICENSE file at the
# root of this project or https://opensource.org/license/bsd-3-clause for the
# full license text.

# Parse the command line arguments.

args <- commandArgs(trailingOnly = TRUE)

if (length(args) <= 0) {
  stop("The TCP port to listen on must be given as the first command line argument.")
}
port <- as.integer(trimws(args[1]))
if (is.na(port)) {
  stop(paste0("Unable to parse '", args[1], "' as a a TCP port number."))
}

if (length(args) <= 1) {
  stop("The R file to plumb must be given as the second command line argument.")
}
rFile <- trimws(args[2])

if (length(args) <= 2) {
  stop("The R library directory must be given as the third command line argument, or \"None\" if the default R library should be used.")
}
rLibrary <- trimws(args[3])

if (length(args) <= 3) {
  stop("The R repository URL must be given as the fourth command line argument.")
}
rRepository <- trimws(args[4])

if (length(args) <= 4) {
  stop("The fifth command line argument must be the list of R packages that should be installed if not already present, or \"None\" if no such packages are required.")
}
userPackages <- trimws(args[5])

if (length(args) <= 5 || (tolower(trimws(args[6])) != "true" && tolower(trimws(args[6])) != "false")) {
  stop("The value \"True\" or \"False\" must be given as the sixth command line argument, indicating whether all R packages should be updated prior to starting plumber.")
}
updateRPackages <- tolower(trimws(args[6]))

if (length(args) <= 6) {
  stop("The authentication token must be given as the seventh command line argument.")
}
authenticationToken <- trimws(args[7])

# If an R library directory was not given, check whether any of the current
# .libPaths() are writable. If not, set rLibrary based on the operating
# system, so that we'll create and use it below.

versionStr <- paste(R.Version()$major, ".", sub("\\..*", "", R.Version()$minor), sep="")

if (tolower(rLibrary) == "none" && !any(file.access(.libPaths(), 2) == 0)) {
  if (grepl("w32", version$os, ignore.case=TRUE)) {
    rLibrary <- file.path(Sys.getenv("LOCALAPPDATA"), "R", "win-library", versionStr)
  } else if (grepl("linux", version$os, ignore.case=TRUE)) {
    rLibrary <- paste0("~/R/", version$platform, "-library/", versionStr, sep="")
  }
  if (tolower(rLibrary) != "none") {
    cat(paste0("None of R's default library directories were writable. The directory ", rLibrary, " will be used instead.\n", sep=""))
  }
}

# If an R library directory was given, check whether it ends in the current
# major.minor version of R (excluding .patch), similar R's default. If it
# does not, add the version number. Then, if it does not exist, create it.
# Then instruct R to use it.

if (tolower(rLibrary) != "none") {
  versionRE <- paste("[/\\\\]", R.Version()$major, "\\.", sub("\\..*", "", R.Version()$minor), "$", sep="")
  if (!grepl(versionRE, rLibrary)) {
    rLibrary <- file.path(rLibrary, versionStr)
  }
  if (!dir.exists(rLibrary)) {
    cat(paste0("Creating R library directory ", rLibrary, "\n", sep=""))
    dir.create(rLibrary, recursive=TRUE)
  }
  .libPaths(rLibrary)
}

# Set the R repository and update the R packages, if requested. On linux,
# package installations often require compiling from source, which takes a
# long time, and sometimes fails if certain C libraries are missing.
# Therefore, on linux, we want quiet=FALSE when updating or installing
# packages. On other platforms, we want quiet=TRUE

options(repos=c(CRAN=rRepository))
quietInstall <- !grepl("linux", version$os, ignore.case=TRUE)
loggedInstallDir <- FALSE

if (updateRPackages == "true") {
  cat("Updating R packages...\n")
  cat(paste0("R packages will be installed to ", .libPaths()[1], "\n", sep=""))
  cat("INSTALLING_R_PACKAGES\n")
  loggedInstallDir <- TRUE

  # Unless the caller has root/administrator access, packages cannot be
  # installed in R's system-wide package directory. In that case,
  # update.packages() is supposed to install them to a personal directory,
  # which will be the first item in .libPaths() by default. Unfortunately,
  # for packages that come in the system-wide directory by default
  # (e.g. installed with R itself), update.packages() will not install
  # updates into the personal directory unless you explicitly set its instlib
  # parameter to that directory (i.e., .libPaths()[1]). So we explicitly do
  # that, even if it seems redundant with our calling .libPaths(rLibrary)
  # above.

  sink(stdout(), type="message")  # Redirect message() to stdout, so it results in INFO rather than WARNING messages
  update.packages(instlib=.libPaths()[1], ask=FALSE, quiet=quietInstall)
  sink(stderr(), type="message")  # Redirect message() back to stderr
}

# Install required packages.

requiredPackages <- c("plumber", "arrow", "tzdb")

if (tolower(userPackages) != "none") {
  for (pkg in strsplit(userPackages, ",")[[1]]) {
    if (!(pkg %in% requiredPackages)) {
      requiredPackages <- c(requiredPackages, pkg)
    }
  }
}

for (pkg in requiredPackages) {
  if (!requireNamespace(pkg, quietly=TRUE)) {
    cat("Installing R package '", pkg, "'...\n", sep="")
    if (!loggedInstallDir) {
      cat(paste0("R packages will be installed to ", .libPaths()[1], "\n", sep=""))
      loggedInstallDir <- TRUE
      cat("INSTALLING_R_PACKAGES\n")
    }
    sink(stdout(), type="message")  # Redirect message() to stdout, so it results in INFO rather than WARNING messages
    install.packages(pkg, quiet=quietInstall)
    sink(stderr(), type="message")  # Redirect message() back to stderr
  }
}

if (loggedInstallDir) {
  cat("DONE_INSTALLING_R_PACKAGES\n")
}

# Load plumber. (The others will be loaded later if needed).

library(plumber)

#' Error handler for plumber that returns a call stack tree in the response.
#'
#' @param req The request object.
#' @param res The response object.
#' @param err The error that was signalled.
#'
errorHandler <- function(req, res, err) {

  # Create a list to return with the response. Following the implementation of
  # the plumber's default handler, if the current res$status is 200
  # (OK), switch it to 500 (Internal Server Error). Otherwise leave it alone,
  # so that other handlers can return 400-series error codes such as 404
  # (Not Found). In either case, set the "error" item to an appropriate
  # message.

  li <- list()

  if (res$status == 200L) {
    res$status <- 500
    li$error <- "500 - Internal server error"
  } else {
    li$error <- "Internal error"
  }

  # Set the "message" item to the string rendering the error that was
  # signalled. If that object includes a "cst" (call stack tree) attribute,
  # set that item as well.

  li$message <- gsub("\\n", "", as.character(err))
  if (!is.null(attr(err, "cst", exact = TRUE))) {
    li$cst <- attr(err, "cst", exact = TRUE)
  }

  # For this response object, transform vectors of length 1 to JSON strings,
  # so that li$error and li$message are serialized as strings rather than as
  # lists containing a single string.

  res$serializer <- serializer_unboxed_json()

  # Return the list. It will be serialized as JSON in the response body.

  li
}

# Start a plumber router on the requested port and R file, using the error
# handler we defined above.

pr(rFile) %>%
  pr_set_error(errorHandler) %>% 
  pr_filter("check_auth_token", function(req, res) {
    if (is.null(req$HTTP_AUTHENTICATION_TOKEN) || req$HTTP_AUTHENTICATION_TOKEN != authenticationToken) {
      res$status <- 401 # Unauthorized
      return(list(error="Missing or invalid authentication token"))
    }
    plumber::forward()
  }) %>%
  pr_run(port = port)
