Notes on ESRI xdoc format
=========================

I ran findstr for `<xdoc>` on `*.rc` in `C:\Program
Files\ArcGIS\Pro\Resources\ArcToolBox\toolboxes` of an Arc Pro 3.2.2 machine
and saved the results in `Development/MGET_test/all_xdoc_rc.txt` on my Linux
dev machine. Then:

```python
inputFile = 'Development/MGET_test/all_xdoc_rc.txt'

with open(inputFile) as f:
    s = f.read()

import re

pattern = r'<\s*\/?\s*([\w\-]+)'
tags = set(re.findall(pattern, s))
for tag in sorted(tags):
    print('<' + tag + '>')
```

Which output:

```xml
<b>
<code>
<entry>
<i>
<img>
<li>
<note>
<ol>
<p>
<para>
<row>
<span>
<table>
<tbody>
<tgroup>
<thead>
<ul>
<xdoc>
```

Here are some notes on each type of element.


`<a>` element
-------------

Classic HTML anchor element. This does not seem to appear in any of ESRI's
tools but Shaun Walbridge of ESRI told me it is supported. Apparently it can
have either of two attributes: `html="url"` or `helpid="ESRI help ID"`. For
the former, I presume any URL is acceptable. For the latter, I suspect we need
to know integer IDs of ESRI help articles.


`<b>` and `<i>` elements
------------------------

Classic HTML bold and italics elements.


`<code>` element
----------------

The only place this appears that I could determine is the "Video Multiplexer"
tool's "Timeshift File" parameter. In [HTML
documentation](https://pro.arcgis.com/en/pro-app/3.2/tool-reference/image-analyst/video-multiplexer.htm),
this is rendered as a traditional code block, But in the pop-up help of the
Arc Pro 3.2.2 Geoprocessing tab, the rendering is broken, and the text appears
at the top rather than after a paragraph much further down.


`<div>` element
---------------

Classic HTML content division element. This does not seem to appear in any of
ESRI's tools but Shaun Walbridge of ESRI told me it is supported. In HTML,
`<div>` generally has no effect unless styles are applied. He mentioned that
the following styles were supported:

```
color:name|#ARGB|Esri_<COLOR>
font-weight:bold
font-size:N
font-style:italic
font-family:fontname
text-indent:N
text-align:{center,right,justify}
width:N
height:N
```

When I tested this, it did not work well. In the in the pop-up help of the Arc
Pro 3.2.2 Geoprocessing tab, the text within the <div> appeared but was not
intended according to text-intent, and no text appeared after the <div>.


`<img>` element
---------------

Classic HTML image elements:

```xml
<p><img src="GUID-3963C531-D744-4CAB-AED4-BA061BAEC0F8-web.png" alt="Full" /></p>
```

The file appears to be loaded from the same directory as the `tool.content.rc`
file, e.g.:

```
C:\Program Files\ArcGIS>dir GUID-3963C531-D744-4CAB-AED4-BA061BAEC0F8-web.png /s
 Volume in drive C has no label.
 Volume Serial Number is 26DC-D48D

 Directory of C:\Program Files\ArcGIS\Pro\Resources\ArcToolBox\toolboxes\Analysis Tools.tbx\Buffer.tool

08/29/2023  06:13 PM             1,686 GUID-3963C531-D744-4CAB-AED4-BA061BAEC0F8-web.png
               1 File(s)          1,686 bytes
```


`<note>` element
----------------

Typical pattern:

```xml
<note type="note"/>
<p group="note">
    <ul>
        <li>If a time is entered without a date, the default date of December 30, 1899, will be used.</li>
        <li>If a date is entered without a time, the default time of 12:00:00 AM will be used.</li>
    </ul>
</p>
```

It appears to be rendered in the in the pop-up help of the Arc Pro 3.2.2
Geoprocessing tab with a piece of paper icon followed by "Note:". The type of
icon and the word that follows depends on the `type` attribute. ArcGIS appears
to support four types:

* `note` - piece of paper
* `license` - key
* `caution` - yellow triangle exclamation point
* `tip` - no icon appears


`<ol>`, `<ul>`, `<li>` elements
-------------------------------

Classic HTML ordered and unordered lists:

```xml
<p>This tool is intended to be used in a workflow with three main steps:
    <ol>
        <li>Run this tool to produce an estimate of the geographic paths used by vehicles in the transit system.</li>
        <li>Use the map to inspect each estimated shape, and use the standard editing tools to make any corrections.</li>
        <li>Run the Features To GTFS Shapes tool to create a shapes.txt file for your GTFS dataset.</li>
    </ol>
</p>
```

```xml
<p>Specifies the unit in which the length will be calculated.</p>
<ul>
    <li><span title="FEET_US">Feet (United States)</span>—Length in feet (United States)</li>
    <li><span title="METERS">Meters</span>—Length in meters</li>
    <li><span title="KILOMETERS">Kilometers</span>—Length in kilometers</li>
    <li><span title="MILES_US">Miles (United States)</span>—Length in miles (United States)</li>
    <li><span title="NAUTICAL_MILES">Nautical miles (United States)</span>—Length in nautical miles (United States)</li>
    <li><span title="YARDS">Yards (United States)</span>—Length in yards (United States)</li>
</ul>
```


`<p>` element
-------------

Classic HTML paragraphs:

```xml
<p>Specifies the unit in which the length will be calculated.</p>
```


`<para>` element
----------------

Appears to be an alternative to `<p>`, but is only used in a single tool,
[Quick Import](https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-interoperability/quick-import.htm).

```xml
<xdoc>
    <para>Converts data in any format supported by the ArcGIS Data Interoperability extension into feature classes.</para>
    <para>The output is stored in a geodatabase. The geodatabase can then be used directly or further post-processing can be performed.</para>
</xdoc>
```


`<span>` element
----------------

This is used very extensively in the documentation of Arc Pro geoprocessing
tools. It appears to be used in several ways. The most common way appears to
be with the `title` attribute, which behaves similarly to HTML: it causes the
title to appear in a tool tip when you hover over the spanned text in the Arc
Pro Geoprocessing tab. (It appears that this attribute is stripped from the
HTML in the online help pages; the `<span>` is there, but the `title`
attribute is not there.) 

A second common use involves assigning styles with the `class` attribute. A
popular class is `esri_uicontrol` attribute, which appears to be rendered in
bold. `esri_fieldname` is also frequently used.

Both of these uses can be seen in the "Spatial Join" tool's "Match Option"
parameter, which starts like this:

```xml
<xdoc>
    <p>Specifies the criteria that will be used to match rows.</p>
        <ul>
        <li><span title="INTERSECT">Intersect</span>—The features in the join features will be matched if they intersect a target feature. This is the default. Specify the distance in the <span class="esri_uicontrol">Search Radius</span> parameter.</li>
        <li><span title="INTERSECT_3D">Intersect 3D</span>— The features in the join features will be matched if they intersect a target feature in three-dimensional space (x, y, and z). Specify the distance in the <span class="esri_uicontrol">Search Radius</span> parameter.</li>
        ...
```

It appears that certain CSS styling can be applied. For example, the
"Transform Field" tool's "Power" parameter applies
`style="vertical-align:sub"`, as shown below. Another tool applies
`style="vertical-align:super"`.

```xml
<xdoc>
    <p>The power parameter ( λ<span style="vertical-align:sub">1</span>) of the Box-Cox transformation. If no value is provided, an optimal value is determined using maximum likelihood estimation (MLE).</p>
</xdoc>
```

It appears to render properly in the in the pop-up help of the Arc Pro 3.2.2
Geoprocessing tab and the HTML documentation. It appears that the same styling
can be applied as for the `<div>` element discussed above, but most of these
styles do not seem to render in the Arc Pro Geoprocessing tab. For example,
`font-family` seems to work, but `font-weight` does not. To get Consolas bold,
`<span class="esri_uicontrol" style="font-family: Consolas">` seems to work
though.


`<table>`, `<tgroup>`, `<thead>`, `<row>`, and `<entry>` elements
-----------------------------------------------------------------

HTML-style markup for tables. It only appears in the "Generate OIS Profile
Data" tool of Aviation Analyst. In [HTML
documentation](https://pro.arcgis.com/en/pro-app/latest/tool-reference/aviation/generate-ois-profile-data.htm)
it renders nicely but I am not licensed for Aviation Analyst so I cannot tell
how it appears in the in the pop-up help of the Arc Pro 3.2.2 Geoprocessing
tab.

```xml
<table>
    <tgroup>
        <thead>
            <row>
                <entry><p>Element paths</p></entry>
                <entry><p>Example</p></entry>
                <entry><p>Populated with</p></entry>
            </row>
        </thead>
        <tbody>
            <row>
                <entry><p>RunwayCenterline</p></entry>
                <entry><p>[-95.9594, 45.5582, 336.6764, 30.0]</p></entry>
                <entry><p>RunwayCenterline point coordinates and elevation at input sampling distance interval [Longitude, Latitude, Elevation, Distance from nearest Runway End]</p></entry>
            </row>
            <row>
                <entry><p>OIS</p></entry>
                <entry><p>[-95.9587, 45.5575, 342.1426, 90.0]</p></entry>
                <entry><p>Obstruction Identification Surface coordinates and altitude at input sampling distance interval [Longitude, Latitude, Elevation, Distance from nearest Runway End]</p></entry>
            </row>
            <row>
                <entry><p>Terrain</p></entry>
                <entry><p>[-95.9592, 45.5579, 338.3926, 338.3926, 338.3926, 30.0]</p></entry>
                <entry><p>Terrain coordinates and elevations across OIS extent at input sampling distance interval [Longitude, Latitude, Minimum Elevation, Elevation along extended runway, Maximum Elevation, Distance from nearest Runway End]</p></entry>
            </row>
            <row>
                <entry><p>Edges</p></entry>
                <entry><p>[-95.958, 45.5578, -95.9594, 45.5572, 90.0]</p></entry>
                <entry><p>Coordinates of OIS edges at opposite sides, outward from runway end at input sampling distance interval [Side 1 Longitude, Side 1 Latitude, Side 2 Longitude, Side 2 Latitude, Distance from nearest Runway End]</p></entry>
            </row>
        </tbody>
    </tgroup>
</table>
```


`<xdoc>` element
----------------

The entire string must be wrapped in `<xdoc>` in order for the other tags to
be recognized:

```xml
<xdoc>
    <p>Specifies whether pyramids will be built for each source raster.</p>
    <ul>
        <li>Unchecked—Pyramids will not be built. This is the default.</li>
        <li>Checked—Pyramids will be built.</li>
    </ul>
</xdoc>
```
