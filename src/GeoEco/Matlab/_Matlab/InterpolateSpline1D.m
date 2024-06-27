function [yi] = InterpolateSpline1D(x, y, xi, method)
% InterpolateSpline1D: wrapper around spline() and pchip()

if method == 1
    yi = spline(x, y, xi);
else
    yi = pchip(x, y, xi);
end
