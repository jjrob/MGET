function [compCurve, dispersalMatrix, settledDensityMatrix, suspendedDensityMatrix, metaData] = DisperseLarvae2012(releaseModel, releaseDate, simulationDuration, simulationTimeStep, summarizationPeriod, competencyGammaA, competencyGammaB, settlementRate, useSensoryZone, diffusivity, sourceIDs, destIDs, reefIDs, reefProps, water, cellSize, uSurface, vSurface, uDepth, vDepth, currentsStartDate, currentsTimeStep)
% DisperseLarvae2012 - simulates the dispersal of larvae from coral reefs using the Treml et al. (2012) algorithm.
%
% ARGUMENTS:
%
% releaseModel - release model for the larvae, either 'A' or 'B'. For 'A',
% 1.0 units of larvae will be released for each grid cell that is 100%
% occupied by reef (i.e. reefProps = 1.0 for that cell). For 'B', 1.0 units
% of larvae are released per entire reef, spread across all of the cells
% occupied by that reef, proportionally according to reefProps.
%
% releaseDate - scalar serial date number or datetime specifying the date and
% time that larvae are released from reefs, e.g. 731065.5 or 
% datetime(2000,10,2,12,0,0) for 2-Oct-2000 12:00:00.
%
% simulationDuration - scalar double that specifies the duration of the
% simulation in days, e.g. 1.5 for a 36 hour simulation.
%
% simulationTimeStep - scalar double that indicates the duration of a
% simulation time step, in days, e.g. 0.0416666667 for 1 hour.
%
% summarizationPeriod - scalar integer that specifies how many simulation
% time steps must pass before another summary of the simulation is
% generated. For example, if the simulationTimeStep is 0.0416666667 (1
% hour) and summarizationPeriod is 24, a the simulation will be summarized
% every 24 hours. Every time the simulation is summarized, a new record is
% added to dispersalMatrix, settledDensityMatrix, and suspendedDensityMatrix.
%
% competencyGammaA - scalar double that specifies the shape parameter (a or
% alpha) of the gamma cumulative distribution function (CDF) used to 
% represent the onset of larval settlement competency, where x is the number
% of days since the simulation started and y is the probability that a larva
% is competent. competencyGammaB, the scale parameter, must also be given.
% Must be 0 or greater. To make larvae immediately fully competent, set 
% competencyGammaA to 0. For more about the gamma function, see 
% https://en.wikipedia.org/wiki/Gamma_distribution.
%
% competencyGammaB - scalar double that specifies the scale parameter (b or
% theta) of the gamma cumulative distribution function (CDF) used to 
% represent the onset of larval settlement competency. Must be 0 or greater.
% Ignored if competencyGammaA is 0.
%
% settlementRate - scalar double that specifies the rate at which competent
% larvae will settle when over reef, expressed as the proportion of larvae
% that will settle per day. This parameter must range between 0 and 1.0.
% For example, the value 0.8 indicates that 80% of the larvae suspended
% over reef for a day will settle.
%
% useSensoryZone - scalar boolean that specifies whether the larvae will
% (true) or will not (false) settle using a sensory zone. If true, all
% larvae in a reef cell will be candidates for settling, regardless of the
% proportion of that cell that is occupied by the reef. Under this scheme,
% it is assumed that the larvae employ a sensory zone that alllows them to
% detect and move to any reef that occurs within the cell they occupy. If
% false, the number of candidate larve will be proportional to the
% proportion of cell that is occupied by the reef. Under this scheme, it is
% assumed that larvae are evenly distributed across the cell they occupy
% and that they do not employ a sensory zone, allowing only the larvae that
% are over the fraction of the cell occupied by reef to settle.
%
% diffusivity - scalar double that indicates the diffusivity constant, in
% m^2/s. This may be zero, in which case diffusion will not be performed,
% greatly speeding up the simulation.
%
% sourceIDs - 1D matrix of integers that are the IDs of the reefs
% from which larvae should be dispersed. Reef IDs must be >= 1 and <=
% 65535. The IDs that appear in this matrix must all appear in the reefIDs
% matrix.
%
% destIDs - 1D matrix of integers that are the IDs of the reefs
% to which larvae could settle. Reef IDs must be >= 1 and <=
% 65535. The IDs that appear in this matrix must all appear in the reefIDs
% matrix.
%
% reefIDs - 2D matrix of integers that maps the locations of coral reefs.
% Each cell contains a reef ID between 1 and 65535, indicating that the
% specified reef occurs in that cell, or 0, indicating that no reef occurs
% in that cell.
%
% reefProps - 2D matrix of singles or doubles ranging from 0.0 to 1.0 that
% indicates the fraction of the cell that is covered by reef (0 = no reef,
% 1.0 = 100% of the cell's area is covered by reef). This matrix must have
% the same dimensions as reefIDs.
%
% water - 2D matrix of logicals or integers that indicate the positions of
% water (1) and land (0). This matrix must have the same dimensions as
% reefIDs.
%
% cellSize - scalar double that indicates the height and width of a cell,
% in meters.
%
% uSurface, vSurface - 3D matrices of singles or doubles that are a time
% series of images of the velocity of ocean currents in the horizontal and
% vertical directions, in m/s, at the surface of the ocean. The matrices
% dimensions are [y,x,t]. The location x=1, y=1 for a given t is the
% upper-left corner of the image, as is traditional with MATLAB. Positive
% values indicating the current is flowing right or up. NaN values indicate
% that no current data is available for the cell; these will be treated as
% having a velocity of 0.
%
% uDepth, vDepth - 3D matrices of singles or doubles that are a time series
% of images of current velocities at the depth that larvae migrate to.
% These matrices have the same dimensions and characteristics of uSurface
% and vSurface. If these matrices are empty (i.e. the [] matrix) then
% vertical migration will not be performed.
%
% currentsStartDate - serial date number or datetime specifying the date and
% time that the first ocean currents image starts, e.g. 731064.5 or 
% datetime(2000,10,1,12,0,0) for 1-Oct-2000 12:00:00.
%
% currentsTimeStep - scalar double that indicates the duration of a
% currents image, in days, e.g. 3.0 for 3 days.
%
% RETURNS:
%
% compCurve - 1D matrix of singles ranging from 0 to 1 that gives the
% proportion of larvae that are competent to settle at each simulation
% time step.
%
% dispersalMatrix - 3D matrix of singles that shows the cumulative
% quantity of larvae dispersed from source reefs to every destination reef,
% at each time the simulation is summarized. The matrix [FROM, TO, t]
% where FROM represents the reef that is the source of larvae, TO
% represents the reef that larvae have settled upon, and t represents the
% summarization period. FROM and TO are indices into sourceIDs and destIDs.
% For example, if sourceIDs/destIDs is [3 6 8], dispersalMatrix(2, 3, :)
% is the larvae released from reef 6 that settled on reef 8. t=1
% corresponds to the start of the simulation when no time steps have
% executed. At t=1, the entire matrix will be zero because no larvae will
% have settled yet. t=2 tallies the cumulative number of larvae that have
% settled after one summarization period has elapsed. t=3 tallies
% the cumulative quantity of larvae that have settled after two summarization
% periods, and so on. For the values of this matrix, 1 unit of larvae is the
% amount released by a reef that fully occupies exactly one grid cell.
%
% settledDensityMatrix - 3D matrix of singles that show the cumulative
% quantity of larvae that have settled throughout the study area at each
% summarization step. The matrix indices are [x,y,t]. Larvae can only settle
% in cells where the reefID is one of the destIDs; the other cells will
% always be zero. t=1 corresponds to the start of the simulation when no time
% steps have executed. At t=1, no larvae will have settled yet, so all cells
% of the matrix will be zero. t=2 tallies the cumulative quantity of larvae
% that have settled after one summarization period has elapsed. t=3 tallies
% the cumulative quantity of larvae that have settled after two summarization
% periods, and so on. For the values of this matrix, 1 unit of larvae is the
% amount released by a reef that fully occupies exactly one grid cell.
%
% suspendedDensityMatrix - 3D matrix of singles that show the instantaneous
% quantity of larvae suspended in the water column (i.e. those that have not
% settled or drifted off the edge of the map yet). The indexing and units of
% this matrix work the same as the settledDensityMatrix. At t=1, all larvae
% will be suspended in the water column over their source reefs. At t>1,
% some larvae will have drifted into other cells.
%
% metaData - a structure array storing all input parameters, stability
% criterion, etc.
%
% REMARKS:
%
% This function does not perform any validation of the input arguments. It
% is up to the caller to pass proper values. For this reason, this function
% is only intended to be called by RunSimulation.m.
%
% HISTORY:
%
% 25-Feb-09 JJR - Initial version created by Eric and Jason in Brisbane.
%
% 26-Feb-09 JJR - Fixed del2 problem. Added courant calculation. Added
%                 copright and license statement.
%
% 23-Nov-09 EAT - Updated finite differencing scheme to the MPDATA 
%                 (multidimensional positive definite advection transport
%                 algorithm). 2nd corrections (3rd optional). See Smolarkiewicz
%                 1983, 1984, and Smolarkiewicz and Margolin 1998
%
% 25-Nov-09 EAT - Added round-off of density surface at 1e-20 to avoid -Inf
%                 single precision errors in flux calculations
%
% 26-Nov-09 EAT - Changed courant condition to stability criteria for 
%                 MPDATA scheme (Smolarkiewicz 1983, Eq. 21)
%
% 21-Jun-10 EAT - Edited description of dispersalMatrix (also in
%                 RunSimulation.m)
%
% 15-Aug-13 EAT - Added metaData structure array to output. Updated Gamma
%                 CDF descriptions
%
% 11-Sep-14 EAT - Implemented ReleaseMode 'B'
%
% 28-Dec-14 EAT - Added sourceIDs and destIDS to enable different source
%                 and destination reefs
%
% 15-Apr-26 JJR - Allow releaseDate and currentsStartDate to be datetimes or
%                 serial date numbers.
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

% Convert datetimes to serial date numbers.

if isdatetime(releaseDate)
    releaseDate = datenum(releaseDate);
elseif ~(isnumeric(releaseDate) && isscalar(releaseDate) && isfinite(releaseDate))
    error('releaseDate must be either a scalar serial date number or a scalar datetime.');
end

if isdatetime(currentsStartDate)
    currentsStartDate = datenum(currentsStartDate);
elseif ~(isnumeric(currentsStartDate) && isscalar(currentsStartDate) && isfinite(currentsStartDate))
    error('currentsStartDate must be either a scalar serial date number or a scalar datetime.');
end

% Ensure that multithreaded processing is enabled. Depending on the version
% of MATLAB we are using, it may already be enabled by default.

maxNumCompThreads('automatic');

% Create destReefIDs from reefIDs and  mask all values that are not
% in the destIDs list. 

% reefIDs(~ismember(reefIDs, reefIDsToSimulate)) = 0;
destReefIDs = reefIDs;
destReefIDs(~ismember(reefIDs, destIDs)) = 0;

% For each source reef ID, obtain the indices into the reefIDs for the cells
% of that reef.
% Also, if releaseMode == B, then set up new matrix
if releaseModel == 'B'
    reefPropsB = single(zeros(size(reefProps)));
end

indicesIntoSourceReefIDsImage = cell(length(sourceIDs), 1);
TotalRelease = single(zeros(length(sourceIDs),1));
for rIndex = 1:length(sourceIDs)
    indicesIntoSourceReefIDsImage{rIndex} = find(reefIDs == sourceIDs(rIndex));
    %Calculate new reefProps if ReleaseMode == B
    if releaseModel == 'B'
        totProps = sum(reefProps(indicesIntoSourceReefIDsImage{rIndex}));
        reefPropsB(indicesIntoSourceReefIDsImage{rIndex}) =  reefProps(indicesIntoSourceReefIDsImage{rIndex})/totProps;
        TotalRelease(rIndex) = sum(reefPropsB(indicesIntoSourceReefIDsImage{rIndex}));
    else
        TotalRelease(rIndex) = sum(reefProps(indicesIntoSourceReefIDsImage{rIndex}));
    end
end

indicesIntoDestinationReefIDsImage = cell(length(destIDs), 1);
for rIndex = 1:length(destIDs)
    indicesIntoDestinationReefIDsImage{rIndex} = find(reefIDs == destIDs(rIndex));
end

% In the ocean currents images, NaN values represent cells for which no
% data is available. We will treat these cells as having currents with a
% velocity of zero. Larvae cannot leave these cells by advection, only by
% diffusion. If any water or reef cells contain NaN, warn the user.

foundNaNWater = false;
reefCellIsNaN = false(size(reefIDs));

for i = 1:size(uSurface, 3)
    if any(any(water(isnan(uSurface(:,:,i)) == 1))) || any(any(water(isnan(vSurface(:,:,i)) == 1)))
        foundNaNWater = true;
    end
    reefCellIsNaN = reefCellIsNaN | (reefIDs ~= 0 & (isnan(uSurface(:,:,i)) | isnan(vSurface(:,:,i))));
end

if foundNaNWater
    if any(any(reefCellIsNaN))
        nanReefIDs = unique(reefIDs(reefCellIsNaN));
        nanReefIDsString = sprintf('%i', nanReefIDs(1));
        if length(nanReefIDs) > 1
            for i = 2:length(nanReefIDs)
                nanReefIDsString = sprintf('%s, %i', nanReefIDsString, nanReefIDs(i));
            end
        end
        warning('The ocean currents images are missing data for some cells flagged as habitat patches. This will affect the accuracy of the simulation. The simulator will assume the ocean currents have a velocity of zero in these cells. Larvae can only exit these cells via diffusion. These cells may retain larvae in a manner that is not realistic. The IDs of the affected patches are: %s', nanReefIDsString)
    else
        warning('The ocean currents images are missing data for some cells flagged as water by your water mask. This will affect the accuracy of the simulation. The simulator will assume the ocean currents have a velocity of zero in these cells. Larvae that enter these cells can only exit via diffusion. These cells may retain larvae in a manner that is not realistic.')
    end
end

uSurface(isnan(uSurface) | isnan(vSurface)) = 0;
vSurface(isnan(uSurface) | isnan(vSurface)) = 0;

% In this simulation, we do not want larvae to advect onto land cells. To
% achieve this, zero out all current vector components that point at land.
% For example, if a water cell has a land cell adjacent on the left, larvae
% will advect onto the land cell if u is negative in the water cell. Set
% this negative u to zero.

neighborIsWater = circshift(water, [-1 0]);                                         % Shift water mask up to get matrix that indicates if below neighbor is water
neighborIsWater(size(neighborIsWater,1),:) = 1;                                     % Assume row of cells below study are are all water
for i = 1:size(vSurface,3)
    vSurface(:,:,i) = vSurface(:,:,i) .* (neighborIsWater | vSurface(:,:,i) > 0);   % Do not zero out V if below neighbor is water or V is flowing up
end

neighborIsWater = circshift(water, [1 0]);                                          % Shift water mask down to get matrix that indicates if above neighbor is water
neighborIsWater(1,:) = 1;                                                           % Assume row of cells above study are are all water
for i = 1:size(vSurface,3)
    vSurface(:,:,i) = vSurface(:,:,i) .* (neighborIsWater | vSurface(:,:,i) < 0);   % Do not zero out V if above neighbor is water or V is flowing down
end

neighborIsWater = circshift(water, [0 -1]);                                         % Shift water mask left to get matrix that indicates if right neighbor is water
neighborIsWater(:,size(neighborIsWater,2)) = 1;                                     % Assume row of cells to right of study are are all water
for i = 1:size(uSurface,3)
    uSurface(:,:,i) = uSurface(:,:,i) .* (neighborIsWater | uSurface(:,:,i) < 0);   % Do not zero out U if right neighbor is water or U is flowing left
end

neighborIsWater = circshift(water, [0 1]);                                          % Shift water mask right to get matrix that indicates if left neighbor is water
neighborIsWater(:,1) = 1;                                                           % Assume row of cells to left of study are are all water
for i = 1:size(uSurface,3)
    uSurface(:,:,i) = uSurface(:,:,i) .* (neighborIsWater | uSurface(:,:,i) > 0);   % Do not zero out U if left neighbor is water or U is flowing right
end

% Calculate stability condition as in Smolarkiewicz 1983 (Eq. 21)
% courant = max(|Uij| + |Vij|) * deltaT / deltaX -EAT
deltaX = cellSize; %-EAT
deltaT = simulationTimeStep * 86400; % simulationTimeStep in days, converted to seconds 

stability = max(max(max((((uSurface.^2) + (vSurface.^2))*((deltaT^2)/deltaX^2)).^.5)));
stabilityError = 0; %Flips to 1 if negative densities are found
if stability <= 2^-.5; %.7071
    fprintf('The stability condition is %f, which is less than or equal to 2 ^ -1/2 = 0.707106. The simulation will be numerically stable.\n', stability)
else
    maxSimulationTimeStep = ((2^-.5)*deltaX)/(max(max(max(uSurface.^2 + vSurface.^2)))^.5)/86400;
    warning('The stability condition is %f, which is greater than 2 ^ -1/2 = 0.707106. The simulation MAY NOT be numerically stable and the output results MAY NOT be correct. To fix this problem, reduce the simulation time step to %f days or less.\n', stability, maxSimulationTimeStep)
end

% courant = maxAbsUV * (simulationTimeStep * 86400) / cellSize;
% if courant <= 1.0
%     fprintf('The courant number is %f, which is less than or equal to 1. The simulation will be numerically stable.\n', courant)
% else
%     maxSimulationTimeStep = cellSize / (maxAbsUV * 86400);
%     warning('The courant number is %f, which is greater than 1. The simulation will NOT be numerically stable and the output results will NOT be correct. To fix this problem, reduce the simulation time step to %f days or less.\n', courant, maxSimulationTimeStep)
% end

% TODO: Add support for vertical migration.

if ~isempty(uDepth) || ~isempty(vDepth)
    error('Vertical migration is not yet implemented.')
end

% Initialize constants used in larval dispersal calculations.

alpha = (simulationTimeStep * 86400) / cellSize;    % deltaT/deltaX in seconds / meter 
K = diffusivity * (simulationTimeStep * 86400);     % m^2
er = 1e-15;                                         % error term in MPDATA

numTimeSteps = floor(simulationDuration / simulationTimeStep);
numSummaries = floor(numTimeSteps / summarizationPeriod) + 1;      % +1 because the first summary is before any time steps have elapsed.

% Calculate the competency for each time step.

compCurve = single(gamcdf(simulationTimeStep .* (1:numTimeSteps), competencyGammaA, competencyGammaB));     % Requires MATLAB Statistics Toolbox

% Allocate the matrices that we will return.

dispersalMatrix = zeros(length(sourceIDs), length(destIDs), numSummaries, 'single');
settledDensityMatrix = zeros(size(reefIDs,1), size(reefIDs,2), numSummaries, 'single');
suspendedDensityMatrix = zeros(size(reefIDs,1), size(reefIDs,2), numSummaries, 'single');

% Simulate the dispersal of larvae for each reef, one at a time.

fprintf('Simulating larval dispersal for %i larval source patches...\n', length(sourceIDs))
progressCookie = StartProgressTimer(length(sourceIDs), 'Still simulating: %s elapsed, %i patches simulated, %s per patch, %i patches remaining, estimated completion time: %s\n', 'Simulation complete: %s elapsed, %i patches simulated, %s per patch.\n');

for rIndex = 1:length(sourceIDs)
    reefID = sourceIDs(rIndex);
    
    % Initialize the matrix D, representing the quantity of larve suspended
    % in the water column at each cell of the study area. Initially, all
    % larvae are suspended over the source reef's cells.
    
    if releaseModel == 'A'
        D = reefProps .* (reefIDs == reefID);
    else
        D = reefPropsB .* (reefIDs == reefID);
    end
    
    % Initialize the matrix S representing the cumulative quantity of
    % larvae settled at each cell of the study area. Initially, no larvae
    % have settled.
    
    S = zeros(size(reefIDs,1), size(reefIDs,2), 'single');
    
    % Determine the rectangular extent of the initial larvae release and
    % buffer it by 1 cell on all sides. This buffered extent defines the
    % cells that larvae can possibly spread to during a single time step,
    % assuming the courant number is less than 1 (as it should be if the
    % simulation is to be stable). To minimize run time, we only perform
    % dispersal calculations within this extent. We will expand it by one
    % cell each time step.
    
    [row, col] = find(D > 0);
    if length(row) <= 0
        warning('No cells of patch %i contain any habitat; the patch cover raster is zero for every cell of this patch. As a result, no larvae will be released from this patch, and no larvae will settle on it.\n', reefID);
        continue
    end
    top = max(min(row)-1, 1);
    bottom = min(max(row)+1, size(D, 1));
    left = max(min(col)-1, 1);
    right = min(max(col)+1, size(D, 2));
    
    % Update the first image in the suspendedDensityMatrix matrix with the initial
    % larvae density.
    
    suspendedDensityMatrix(top:bottom, left:right, 1) = suspendedDensityMatrix(top:bottom, left:right, 1) + D(top:bottom, left:right);
    
    % Loop through each time step. 
    
    lastCurrentsIndex = 0;
    
    for ts = 1:numTimeSteps
        
        % Compute the index into stack of ocean currents images for this
        % time step.
        
        newCurrentsIndex = floor((releaseDate - currentsStartDate + (ts-1)*simulationTimeStep) / currentsTimeStep) + 1;
        
        % If this time step has switched to a different ocean currents
        % image, get the data. Calculate velocity at top, bottom, left,
        % and right cell walls (VT, VB, UL, UR) -EAT
        
        if newCurrentsIndex ~= lastCurrentsIndex 
            U = uSurface(:, :, newCurrentsIndex);
            V = vSurface(:, :, newCurrentsIndex);
            
            % Calculate average currents at cell walls
            CurrL = circshift(U, [0 1]);                    % Shift Currents Right
            ULfull = (U + CurrL)/2;                        % Ave velocity at Left wall
            CurrR = circshift(U,[0 -1]);                    % Shift Currents to Left
            URfull = (U + CurrR)/2;                        % Ave velocity at Right wall
            absULfull = abs(ULfull);
            absURfull = abs(URfull);
            CurrT = circshift(V, [1 0]);                    % Shift Currents Down
            VTfull = (V + CurrT)/2;                        % Ave velocity at Top wall
            CurrB = circshift(V,[-1 0]);                    % Shift Currents to Up
            VBfull = (V + CurrB)/2;                        % Ave velocity at Bottom wall
            absVTfull = abs(VTfull);
            absVBfull = abs(VBfull);
            
            % Calculate the implicit numerical diffusivity at cell walls
            KimpLfull = -.5*((absULfull*deltaX) - (deltaT*(ULfull.^2)));
            KimpRfull = -.5*((absURfull*deltaX) - (deltaT*(URfull.^2)));
            KimpBfull = -.5*((absVBfull*deltaX) - (deltaT*(VBfull.^2)));
            KimpTfull = -.5*((absVTfull*deltaX) - (deltaT*(VTfull.^2)));

            lastCurrentsIndex = newCurrentsIndex;
        end
        
        % Extract the absolute ocean current velocities and directions for
        % the subset of the larger matrix that larvae could have possibly
        % spread to.
        
        UL = ULfull(top:bottom, left:right);
        UR = URfull(top:bottom, left:right);
        absUL = absULfull(top:bottom, left:right);
        absUR = absURfull(top:bottom, left:right);
        VT = VTfull(top:bottom, left:right);
        VB = VBfull(top:bottom, left:right);
        absVT = absVTfull(top:bottom, left:right);
        absVB = absVBfull(top:bottom, left:right);
        KimpL = KimpLfull(top:bottom, left:right);
        KimpR = KimpRfull(top:bottom, left:right);
        KimpB = KimpBfull(top:bottom, left:right);
        KimpT = KimpTfull(top:bottom, left:right);
 
        
        % Initialize the suspended larvae density matrix for this time step
        % to the matrix for the last time step, limited to the subset of
        % the larger matrix that larvae could have possibly spread to.
        
        subsetD = D(top:bottom, left:right);
        roundD = subsetD > 1e-20;                                       % Drop extremely low densities
        newD = subsetD.*roundD; 
%         newD = subsetD;

        % MPDATA Code Start -EAT   
        % Calc Flux in/out at cell walls &  take first trial upwind step 
            DtoL = circshift(newD, [0 1]); DtoL(:,1) = 0;               % Density to Left
            FL = ((UL + absUL).*DtoL + (UL - absUL).*newD)*.5*alpha;  % Flux at Left Wall
            DtoR = circshift(newD, [0 -1]); DtoR(:,end) = 0;            % Density to Right
            FR = ((UR + absUR).*newD + (UR - absUR).*DtoR)*.5*alpha;  % Flux at Right Wall
            
            DtoB = circshift(newD, [-1 0]); DtoB(end,:) = 0;            % Density to Bottom
            FB = ((VB + absVB).*DtoB + (VB - absVB).*newD)*.5*alpha;  % Flux at Bottom Wall
            DtoT = circshift(newD, [1 0]); DtoT(1,:) = 0;               % Density to Top
            FT = ((VT + absVT).*newD + (VT - absVT).*DtoT)*.5*alpha;  % Flux at Top Wall
            
%             newD = newD - (FR - FL) - (FT - FB);                        % 1st upwind estimate
             newD = newD - (FR - FL + FT - FB);

            %ERROR CHECKING
            neg = min(min((newD)));
            if neg < 0
               warning('During simulation of patch %i, a negative density was detected during step %i of the simulation. This indicates a numerical stability problem with the MPDATA algorithm. You should reduce the simulation time step to a lower value and try again. If this does not resolve the problem, please contact the MGET development team for assistance.\n', reefID, ts);
               stabilityError = 1;
            end
             
            for cor = 1:2;                                              % first correction (change to 1:2 for second correction)
            PosnewD = find(newD > 0);                                   % all positive Cest cells            

                % Calculate anti-diffusion velocity (Vd) at cell walls 
                %Left wall
                newDL = circshift(newD, [0 1]); newDL(:,1) = 0;
                dCdxL = zeros(size(newD));  
                dCdxL(PosnewD) = (newD(PosnewD) - newDL(PosnewD))./(newD(PosnewD) + newDL(PosnewD)+er)/deltaX;
                VdL = -KimpL.*dCdxL;                                    % antidiffusion velocity
                absVdL = abs(VdL);

                %Right wall
                newDR = circshift(newD, [0 -1]); newDR(:,end) = 0;
                dCdxR = zeros(size(newD));  
                dCdxR(PosnewD) = (newDR(PosnewD) - newD(PosnewD))./(newDR(PosnewD) + newD(PosnewD)+er)/deltaX;
                VdR = -KimpR.*dCdxR;                                    % antidiffusion velocity
                absVdR = abs(VdR);

                %Bottom wall
                newDB = circshift(newD, [-1 0]); newDB(end,:) = 0;
                dCdxB = zeros(size(newD));  
                dCdxB(PosnewD) = (newD(PosnewD) - newDB(PosnewD))./(newD(PosnewD) + newDB(PosnewD)+er)/deltaX;
                VdB = -KimpB.*dCdxB;                                    % antidiffusion velocity
                absVdB = abs(VdB);

                %Top wall
                newDT = circshift(newD, [1 0]); newDT(1,:) = 0;
                dCdxT = zeros(size(newD));  
                dCdxT(PosnewD) = (newDT(PosnewD) - newD(PosnewD))./(newDT(PosnewD) + newD(PosnewD)+er)/deltaX;
                VdT = -KimpT.*dCdxT;                                    % antidiffusion velocity
                absVdT = abs(VdT);

                % Calculate anti-diffusion flux (Fd) at cell walls
                FdL = (((VdL + absVdL).*newDL) + ((VdL - absVdL).*newD))*.5*alpha;
                FdR = (((VdR + absVdR).*newD) + ((VdR - absVdR).*newDR))*.5*alpha;
                FdB = (((VdB + absVdB).*newDB) + ((VdB - absVdB).*newD))*.5*alpha;
                FdT = (((VdT + absVdT).*newD) + ((VdT - absVdT).*newDT))*.5*alpha;

                % Calculate corrected D estimate at time + 1
%                 newD = newD - (FdR - FdL) - (FdT - FdB); %Nov24 change
                        % newD -FdR + FdL - FdT + FdB
                newD = newD - (FdR - FdL + FdT - FdB);
                        % newD - FdR + FdL - FdT + FdB
            end;
   
        % MPDATA Code Ends  
        

        % If the caller passed in a diffusivity coefficient, account for
        % larvae diffused in from or out to neighboring cells. If they did
        % not pass in a diffusivity coefficient, skip diffusion, which will
        % greatly speed up the simulation. In order to avoid edge effects
        % introduced by the del2 function, we must buffer subsetD by three
        % pixels of zeros on all sides before calling del2.

        if diffusivity > 0
            bufferedSubsetD = zeros(size(newD) + 6, 'single');
            bufferedSubsetD(4:size(subsetD,1)+3, 4:size(subsetD,2)+3) = subsetD;
            bufferedSubsetD = K*4*del2(bufferedSubsetD, cellSize);
            newD = newD + bufferedSubsetD(4:size(subsetD,1)+3, 4:size(subsetD,2)+3);
        end
        
        % Zero out cells that are land. Larvae that have diffused to land
        % cells are lost. (In the future, we may adjust the del2
        % calculation above to avoid diffusing onto land. We already avoid
        % advecting onto land.)
        
        newD(water(top:bottom, left:right) == 0) = 0;

        % Compute the larvae that have settled during this time step. If
        % we're using the sensory zone, all of the larve within a cell can
        % settle. (Even if the reef only occupies a small fraction of the
        % cell, the larvae will swim to that reef.) If we're not using the
        % sensory zone, only the fraction of larvae that are over the
        % portion of the cell covered by reef can settle.

        if useSensoryZone
            stepS = compCurve(ts) .* (destReefIDs(top:bottom, left:right) > 0) .* newD .* settlementRate .* simulationTimeStep;
        else
            stepS = compCurve(ts) .* (destReefIDs(top:bottom, left:right) > 0) .* newD .* settlementRate .* simulationTimeStep .* reefProps(top:bottom, left:right);
        end

        % Subtract the larvae that have settled from the larvae in the
        % water

        newD = newD - stepS;
        S(top:bottom, left:right) = S(top:bottom, left:right) + stepS;
        
        % Update the full-sized matrix of suspended larvae (D) with the
        % new values.
        
        D(top:bottom, left:right) = newD;
    
        % If we have executed a sufficient number of time steps, summarize
        % the simulation by adding records to dispersalMatrix, settledDensityMatrix
		% and suspendedDensityMatrix. 

        if rem(ts, summarizationPeriod) == 0
            for toReefIndex = 1:length(destIDs)
                dispersalMatrix(rIndex, toReefIndex, 1 + ts/summarizationPeriod) = sum(S(indicesIntoDestinationReefIDsImage{toReefIndex}));
            end
            settledDensityMatrix(top:bottom, left:right, 1 + ts/summarizationPeriod) = settledDensityMatrix(top:bottom, left:right, 1 + ts/summarizationPeriod) + S(top:bottom, left:right);        % = settled larvae from previously-simulated reefs + settled larvae from the focal reef, both cumulative since t=1
            suspendedDensityMatrix(top:bottom, left:right, 1 + ts/summarizationPeriod) = suspendedDensityMatrix(top:bottom, left:right, 1 + ts/summarizationPeriod) + newD;                         % = suspended larvae from previously-simulated reefs + suspended larvae from the focal reef, both instantaneous at this time step (NOT cumulative since t=1)
        end
        
        % Increase the possible extent that the larvae have spread to by
        % one cell in all directions. Larvae are guaranteed to have spread
        % in these directions by diffusion, even if advection is flowing
        % the other direction or not at all.
        
        top = max(top - 1, 1);
        bottom = min(bottom + 1, size(D, 1));
        left = max(left - 1, 1);
        right = min(right + 1, size(D, 2));
    end
    
    % Report our progress after 1 minute and every 5 minutes thereafter.

    progressCookie = ReportProgress(progressCookie);
end

% Create and fill metaData structure
metaData.releaseModel = releaseModel;
metaData.TotalRelease = TotalRelease;
metaData.releaseDate = datestr(releaseDate, 'yyyy-mm-dd HH:MM:SS');
metaData.simulationDuration = simulationDuration;
metaData.simulationTimeStep = simulationTimeStep;
metaData.summarizationPeriod = summarizationPeriod;
metaData.competencyGammaA = competencyGammaA;
metaData.competencyGammaB = competencyGammaB;
metaData.settlementRate = settlementRate;
metaData.useSensoryZone = useSensoryZone;
metaData.diffusivity = diffusivity;
metaData.sourceIDs = sourceIDs;
metaData.destIDs = destIDs;
metaData.cellSize = cellSize;
metaData.currentsTimeStep = currentsTimeStep;
metaData.stability = stability;
metaData.stabilityError = stabilityError;