function TestLogging()
% TestLogging: Test that we properly capture output and log it, when called from Python

disp("Informational message 1")
pause(5)
warning("Warning 1")
pause(1)
disp("Informational message 2")
pause(1)
warning("Warning 2")
pause(1)
