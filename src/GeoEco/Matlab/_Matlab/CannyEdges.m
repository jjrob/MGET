function [result] = CannyEdges(a, lowThreshIn, highThreshIn, sigma, minSize)
% CannyEdges: Canny edge detector with absolute thresholds and NaN support.

% Inpaint NaNs (using the fastest algorithm).

aOriginal = a;
a = InpaintNaNs(a, 2, 0, false, NaN, NaN);

% Detect edges with the MATLAB edge function from the image processing toolbox.

if (highThreshIn == -1) && (lowThreshIn == -1)
    threshIn = [];
elseif lowThreshIn == -1
    threshIn = highThreshIn;
else
    threshIn = [lowThreshIn, highThreshIn];
end

if sigma == -1
    [e, threshOut] = edge(a, 'Canny', threshIn);
else
    [e, threshOut] = edge(a, 'Canny', threshIn, sigma);
end

if (highThreshIn == -1) && (lowThreshIn == -1)
    lowThresh = threshOut(1);
    highThresh = threshOut(2);
elseif lowThreshIn == -1
    lowThresh = threshOut(1);
    highThresh = highThreshIn;
else
    lowThresh = lowThreshIn;
    highThresh = highThreshIn;
end

% Remove small edges.

if minSize >= 2
    e(isnan(aOriginal)) = 0;
    e = bwareaopen(e, minSize, 8);
end

% Put the NaNs back into the image.

e = single(e);
e(isnan(aOriginal)) = nan;

% Return the edges array and thresholds as a cell array

result = {e lowThresh highThresh};
