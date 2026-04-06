function b = TestIsMember(a)
% TestIsMember: Test that the ismember() function works when called from Python; we had a problem with this in MATLAB R2026a

if ismember(a, 0:5)
    b = 1;
else
    b = 0;
end
