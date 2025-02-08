<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="xml" omit-xml-declaration="yes"/>

    <xsl:template match="block_quote">
        <div style="text-indent: 3em each-line">
            <xsl:apply-templates/>
        </div>
    </xsl:template>

    <xsl:template match="bullet_list">
        <ul>
            <xsl:apply-templates/>
        </ul>
    </xsl:template>

    <xsl:template match="document">
        <xdoc>
            <xsl:apply-templates/>
        </xdoc>
    </xsl:template>

    <xsl:template match="enumerated_list">
        <ol>
            <xsl:apply-templates/>
        </ol>
    </xsl:template>

    <xsl:template match="list_item">
        <li>
            <xsl:apply-templates/>
        </li>
    </xsl:template>

    <xsl:template match="literal">
        <span class="esri_uicontrol" style="font-family: Consolas">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template match="literal_block">
        <pre>
            <xsl:apply-templates/>
        </pre>
    </xsl:template>

    <xsl:template match="paragraph[not(parent::warning)]">
        <p>
            <xsl:apply-templates/>
        </p>
    </xsl:template>

    <xsl:template match="reference">
        <a href="{@refuri}">
            <xsl:apply-templates/>
        </a>
    </xsl:template>

    <xsl:template match="superscript">
        <span style="vertical-align:super">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template match="subscript">
        <span style="vertical-align:sub">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template match="strong">
        <b>
            <xsl:apply-templates/>
        </b>
    </xsl:template>

    <xsl:template match="warning">
        <note type="warning"/>
        <xsl:apply-templates/>
    </xsl:template>

    <xsl:template match="warning/paragraph">
        <p group="warning">
            <xsl:apply-templates/>
        </p>
    </xsl:template>

    <!-- Table-related elements -->
    <xsl:template match="table | tgroup | thead | tbody | row | entry">
        <xsl:copy>
          <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
    </xsl:template>

    <xsl:template match="colspec"/>

    <!-- Ignore target elements -->
    <xsl:template match="target"/>

    <!-- These are used for items enclosed in single backticks, e.g.
         `overwriteExisting`. We render these in italics. Typically these are
         the names of method parameters. After transforming the XSL, we look
         for instances of <i>parameterName</i> and replace them with the
         ArcGISDisplayName of the parameter. -->
    <xsl:template match="title_reference">
        <i>
            <xsl:apply-templates/>
        </i>
    </xsl:template>

    <!-- Default template to catch unrecognized elements and fail -->
    <xsl:template match="*">
        <xsl:message terminate="yes">
            Unrecognized element: <xsl:value-of select="name()"/>
        </xsl:message>
    </xsl:template>

    <!-- Template to replace newlines with <br/> in literal elements and spaces in all others -->
    <xsl:template match="text()" name="replaceNewLines">
        <xsl:choose>
            <xsl:when test="parent::literal or parent::literal_block">
                <xsl:call-template name="string-replace-newline-with-br">
                    <xsl:with-param name="text" select="." />
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="translate(., '&#10;', ' ')"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- Template that does replaces all instances of a the newline character with <br/> in a string, compatible with XSLT 1.0 -->
    <xsl:template name="string-replace-newline-with-br">
        <xsl:param name="text" />
        <xsl:choose>
            <xsl:when test="contains($text, '&#10;')">
                <xsl:value-of select="substring-before($text, '&#10;')" />
                <br/>
                <xsl:call-template name="string-replace-newline-with-br">
                    <xsl:with-param name="text" select="substring-after($text, '&#10;')" />
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$text" />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

</xsl:stylesheet>
