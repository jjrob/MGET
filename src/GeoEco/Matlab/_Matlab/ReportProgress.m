function updatedCookie = ReportProgress(cookie)
% ReportProgress - reports on the progress of an iterative process
%
% ARGUMENTS:
%
% cookie - a cookie structure returned by StartProgressTimer
%
% HISTORY:
%
% 25-Feb-09 JJR - Initial version created by Eric and Jason in Brisbane.
%
% 26-Feb-09 JJR - Added copright and license statement.
%
% COPYRIGHT AND LICENSE:
%
% Copyright (C) 2009 Eric A Treml and Jason J. Roberts
%
% This program is free software; you can redistribute it and/or
% modify it under the terms of the GNU General Public License
% as published by the Free Software Foundation; either version 2
% of the License, or (at your option) any later version.
%
% This program is distributed in the hope that it will be useful,
% but WITHOUT ANY WARRANTY; without even the implied warranty of
% MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
% GNU General Public License (available in the file LICENSE.TXT)
% for more details.
%
% You should have received a copy of the GNU General Public License
% along with this program; if not, write to the Free Software
% Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

% Increment the number of steps completed.

cookie.stepsCompleted = cookie.stepsCompleted + 1;

% If we reached the total number of steps, report the completion message.

currentTime = now;
if cookie.stepsCompleted >= cookie.numSteps
    elapsedTime = currentTime - cookie.startTime;
    elapsedStr = FormatTime(currentTime - cookie.startTime);

    perStepTime = elapsedTime / cookie.numSteps;
    perStepStr = FormatTime(perStepTime);

    fprintf(cookie.completionMessage, elapsedStr, cookie.numSteps, perStepStr);
    
% Otherwise report the progress message after one minute has elapsed, and
% every five minutes thereafter.

else
    if currentTime >= cookie.nextReportTime
        elapsedTime = currentTime - cookie.startTime;
        elapsedStr = FormatTime(currentTime - cookie.startTime);

        perStepTime = elapsedTime / cookie.stepsCompleted;
        perStepStr = FormatTime(perStepTime);

        completionTime = currentTime + (cookie.numSteps - cookie.stepsCompleted) * perStepTime;
        if fix(completionTime) ~= fix(currentTime)
            completionStr = datestr(completionTime, 'dd-mmm-yyyy HH:MM:SS');
        else
            completionStr = datestr(completionTime, 'HH:MM:SS');
        end

        fprintf(cookie.progressMessage, elapsedStr, cookie.stepsCompleted, perStepStr, cookie.numSteps - cookie.stepsCompleted, completionStr);

        cookie.nextReportTime = currentTime + 1/86400 * 300;
    end
end

updatedCookie = cookie;


function s = FormatTime(t)
% FormatTime - formats a time duration in a compact, easy-to-read form
if t < 1/1440
    s = strcat(datestr(t, 'SS.FFF'), ' seconds');
elseif t < 1/24
    s = datestr(t, 'MM:SS');
elseif t < 1
    s = datestr(t, 'HH:MM:SS');
else
    s = sprintf('%i days, %s', fix(t), datestr(rem(t,1), 'HH:MM:SS'));
end
