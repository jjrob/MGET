function cookie = StartProgressTimer(numSteps, progressMessage, completionMessage)
% StartTimedProcess - starts a timer that tracks the progress of an iterative process 
%
% ARGUMENTS:
%
% numSteps - number of iterations that will be performed
%
% progressMessage - the message to report when progress is periodically
% reported, such as:
%
%     'Still loading: %s elapsed, %i images loaded, %s per image, %i images remaining, estimated completion time: %s\n'
%
% The message must contain the same sequence of format specifiers shown in
% the example above.
%
% completionMessage - the message to report when all processing steps have
% been performed, such as:
%
%     'Loading complete: %s elapsed, %i images loaded, %s per image.\n'
%
% The message must contain the same sequence of format specifiers shown in
% the example above.
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

if numSteps <= 0
    error('The number of steps must be greater than 0.')
end

cookie.numSteps = numSteps;
cookie.stepsCompleted = 0;
cookie.progressMessage = progressMessage;
cookie.completionMessage = completionMessage;
cookie.startTime = now;
cookie.nextReportTime = cookie.startTime + 1/86400 * 60;
