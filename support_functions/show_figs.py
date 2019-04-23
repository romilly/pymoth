def getScreen():
    '''
    function to get screen width and height (linux/mac compatible)
    '''
    # tkinter errors if run after matplotlib is loaded, so run it first
    import tkinter as tk
    root = tk.Tk()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.update()
    root.destroy()
    return (screen_width, screen_height)

def showFeatureArrayThumbnails( featureArray, showPerClass, normalize, titleString ):
    '''
    Show thumbnails of inputs used in the experiment.
    Inputs:
        1. featureArray = either 3-D
            (1 = cols of features, 2 = within class samples, 3 = class)
            or 2-D (1 = cols of features, 2 = within class samples, no 3)
        2. showPerClass = how many of the thumbnails from each class to show.
        3. normalize = 1 if you want to rescale thumbs to [0 1], 0 if you don't
        4. titleString = string
    '''

    # tkinter errors if run after matplotlib is loaded, so we run it first
    scrsz = getScreen()

    import numpy as np
    import matplotlib.pyplot as plt

    # bookkeeping: change dim if needed
    # DEV NOTE: Clarify with CBD - this seems unnecessary
    if len(featureArray.shape)==2:
        f = np.zeros((featureArray.shape[0],featureArray.shape[1],1))
        f[:,:,0] = featureArray
        featureArray = f  #.squeeze()

    pixNum, numPerClass, nC  = featureArray.shape
    # DEV NOTE: Should be able to remove classNum from inputs above

    total = nC*showPerClass # total number of subplots
    numRows = np.ceil(np.sqrt(total/2)) # n of rows
    numCols = np.ceil(np.sqrt(total*2)) # n of cols
    vert = 1/(numRows + 1) # vertical step size
    horiz = 1/(numCols + 1) # horizontal step size

    print('screen size: ', scrsz)
    fig_sz = [np.floor((i/100)*0.5) for i in scrsz]
    thumbs = plt.figure(figsize=fig_sz, dpi=100)

    for cl in range(nC): # 'class' is a keyword in Python; renamed to 'cl'
        for i in range(showPerClass):
            ax_i = showPerClass*(cl) + i + 1
            thisInput = featureArray[:, i, cl]

            if normalize:
                # DEV NOTE: This only affects the last image in the stack (the average)
                # -> could be made more efficient
                #print(thisInput.max())
                thisInput /= thisInput.max() # renormalize, to offset effect of classMagMatrix scaling

            ax_count = i + (cl*nC)
            plt.subplot(np.int(numRows),np.int(numCols),ax_i)

            # # DEV NOTE: Rename or delete these
            # # reverse:
            # # thisInput = (-thisInput + 1)*1.1
            # thisCol = ax_i % numCols
            # if thisCol==0:
            #     thisCol = numCols
            # thisRow = np.ceil( ax_i / numCols )

            # a = horiz*(thisCol - 1) # x-coordinates (left edge)
            # b = 1 - vert*(thisRow) # y-coordinates (bottom edge)
            # c = horiz # subplot width
            # d = vert # subplot height

            side = np.int(np.sqrt(len(thisInput)))
            plt.imshow(thisInput.reshape((side,side)), cmap='gray')

    # add a title at the bottom
    plt.xlabel(titleString, fontweight='bold')
    plt.show()

def viewENresponses( simRes, modelParams, expP,
    showPlots, classLabels, resultsFilename=[], saveImageFolder=[] ):
    '''
    View readout neurons (EN):
        Color-code them dots by class and by concurrent octopamine.
        Collect stats: median, mean, and std of FR for each digit, pre- and post-training.
        Throughout, digits may be referred to as odors, or as odor puffs.
        'Pre' = naive. 'Post' = post-training

    Inputs:
        1. simRes: dictionary containing simulation results (output from sdeWrapper)
        2. modelParams: object containing model parameters for this moth
        3. expP: object containing experiment parameters with timing
            and digit class info from the experiment.
        4. showPlots: 1 x 2 vector. First entry: show changes in accuracy. 2nd entry: show EN timecourses.
        5. classLabels: 1 to 10
        6. resultsFilename:  to generate image filenames if saving. Optional argin
        7. saveImageFolder:  where to save images. If this = [], images will not be saved (ie its also a flag). Optional argin.

    Outputs (as fields of resultsStruct):
        1. preMeanResp = numENs x numOdors matrix = mean of EN pre-training
        2. preStdResp = numENs x numOdors matrix = std of EN responses pre-training
        3. ditto for post etc
        4. percentChangeInMeanResp = 1 x numOdors vector
        5. trained = list of indices corresponding to the odor(s) that were trained
        6. preSpontMean = mean(preSpont)
        7. preSpontStd = std(preSpont)
        8. postSpontMean = mean(postSpont)
        9. postSpontStd = std(postSpont)
    '''

    # tkinter errors if run after matplotlib is loaded, so we run it first
    scrsz = getScreen()

    import os
    import numpy as np
    import matplotlib.pyplot as plt

    if saveImageFolder:
        if not os.path.isdir(saveImageFolder):
            os.mkdir(saveImageFolder)

    # nE = modelParams.nE;

    # pre- and post-heb spont stats
    # preHebSpontStart = expP.preHebSpontStart;
    # preHebSpontStop = expP.preHebSpontStop;
    # postHebSpontStart = expP.postHebSpontStart;
    # postHebSpontStop = expP.postHebSpontStop;

    colors = [ (0, 0, 1), (0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 0, 1), (0, 1, 1),
        (1, 0.3, 0.8), (0.8, 0.3, 1), (0.8, 1, 0.3), (0.5, 0.5, 0.5) ] # for 10 classes
    # concurrent octopamine will be marked with yellow x's

    # E = simRes.E;   % # timesteps x #ENs
    # T = simRes.T;   % # timesteps x 1
    # octoHits = simRes.octoHits;

    if simRes['octoHits'].max() > 0:
        octoTimes = simRes['T'][ simRes['octoHits'] > 0 ]
    else:
        octoTimes = []

    # calc spont stats
    preSpont = simRes['E'][ np.logical_and(expP.preHebSpontStart < simRes['T'],
                                    simRes['T'] < expP.preHebSpontStop) ]
    postSpont = simRes['E'][ np.logical_and(expP.postHebSpontStart < simRes['T'],
                                    simRes['T'] < expP.postHebSpontStop) ]

    preHebMean = preSpont.mean()
    preHebStd = preSpont.std()
    postHebMean = postSpont.mean()
    postHebStd = postSpont.std()

    ## Set regions to examine:
    # 1. data from expP
    # simStart = expP.simStart;
    # classMags = expP.classMags;
    # stimStarts = expP.stimStarts; % to get timeSteps from very start of sim
    stimStarts = expP.stimStarts*(expP.classMags > 0) # ie only use non-zero puffs
    # whichClass = expP.whichClass;
    whichClass = expP.whichClass*(expP.classMags > 0)
    # startTrain = expP.startTrain;
    # endTrain = expP.endTrain;

    classList = np.unique(whichClass)
    # numClasses = length(classList);

    # Make one stats plot per EN. Loop through ENs:
    for enInd in range(modelParams.nE):

        thisEnResponse = simRes['E'][:, enInd]

        ## Calculate pre- and post-train odor response stats
        # Assumes that there is at least 1 sec on either side of an odor without octo

        # pre-allocate for loop
        preTrainOdorResp = np.empty(len(stimStarts))
        postTrainOdorResp = np.empty(len(stimStarts))

        for i, t in enumerate(stimStarts):
            # Note: to find no-octo stimStarts, there is a certain amount of machinery
            # in order to mesh with the timing data from the experiment.
            # For some reason octoTimes are not recorded exactly as listed in format
            # short mode. So we need to use abs difference > small thresh, rather
            # than ~ismember(t, octoTimes):
            small = 1e-8 # .00000001
            # assign no-octo, PRE-train response val (or -1)
            preTrainOdorResp[i] = -1 # as flag
            if (len(octoTimes)==0) or ((abs(octoTimes - t).min() > small) and (t < expP.startTrain)):
                resp_ind = np.logical_and(t-1 < simRes['T'], simRes['T'] < t+1)
                preTrainOdorResp[i] = thisEnResponse[resp_ind].max()

            # assign no-octo, POST-train response val (or -1)
            postTrainOdorResp[i] = -1
            if len(octoTimes)!=0:
                if (abs(octoTimes - t).min() > small) and (t > expP.endTrain):
                    resp_ind = np.logical_and(t-1 < simRes['T'], simRes['T'] < t+1)
                    postTrainOdorResp[i] = thisEnResponse[resp_ind].max()

        # pre-allocate for loop
        preMeanResp = preMedianResp = preStdResp = preNumPuffs = np.empty(len(classList))
        postMeanResp = postMedianResp = postStdResp = postNumPuffs = np.empty(len(classList))

        # calc no-octo stats for each odor, pre and post train:
        for k, cl in enumerate(classList):
            curCl = whichClass==cl
            preFull = preTrainOdorResp[np.logical_and(preTrainOdorResp>=0, curCl)]
            postFull = postTrainOdorResp[np.logical_and(postTrainOdorResp>=0, curCl)]
            ## calculate the averaged sniffs of each sample: SA means 'sniffsAveraged'
            # this will contain the average responses over all sniffs for each sample
            # DEV NOTE: Changed pretty drastically, but should be the same.
            # Check with CBD
            preSA = preFull
            postSA = postFull

            if len(preSA)==0: # DEV NOTE: When would this occur? Remove?
                preMeanResp[k] = -1
                preMedianResp[k] = -1
                preStdResp[k] = -1
                preNumPuffs[k] = 0
            else:
                preMeanResp[k] = preSA.mean()
                preMedianResp[k] = np.median(preSA)
                preStdResp[k] = preSA.std()
                preNumPuffs[k] = len(preSA)

            if len(postSA)==0: # DEV NOTE: When would this occur? Remove?
                postMeanResp[k] = -1
                postMedianResp[k] = -1
                postStdResp[k] = -1
                postNumPuffs[k] = 0
            else:
                postMeanResp[k] = postSA.mean()
                postMedianResp[k] = np.median(postSA)
                postStdResp[k] = postSA.std()
                postNumPuffs[k] = len(postSA)

        # # to plot +/- 1 std of % change in meanResp, we want the std of our
        # # estimate of the mean = stdResp/sqrt(numPuffs). Make this calc:
        # preStdMeanEst = preStdResp/np.sqrt(preNumPuffs)
        # postStdMeanEst = postStdResp/np.sqrt(postNumPuffs)

        # could use: (preNumPuffs > 0).nonzero()
        preSA = [i for (i, val) in enumerate(preNumPuffs) if val>0]
        postSA = [i for (i, val) in enumerate(postNumPuffs) if val>0]
        postOffset = [i + 0.25 for i in postSA]

        # a key output:
        percentChangeInMeanResp = (100*(postMeanResp[preSA] - preMeanResp[preSA]))\
                                    /preMeanResp[preSA]
        percentChangeInNoiseSubtractedMeanResp = \
                                (100*(postMeanResp[preSA] - preMeanResp[preSA] - postHebMean))\
                                /preMeanResp[preSA]

        percentChangeInMedianResp = (100*(postMedianResp[preSA] - preMedianResp[preSA]))\
                                /preMedianResp[preSA]
        percentChangeInNoiseSubtractedMedianResp = \
                                (100*(postMedianResp[preSA] - preMedianResp[preSA] - postHebMean))\
                                /preMedianResp[preSA]

        import pdb; pdb.set_trace()
        # create list of xticklabels
        trueXLabels = classLabels
        # trueXLabels = [None] * len(classLabels)
        # for j,c in enumerate(classLabels):
            # trueXLabels[j] = str(c % 10) # 'mod' turns 10 into 0

        # plot stats if wished:
        if showPlots[1]:
            # del = texlabel('Delta');
            fig_sz = [np.floor((i/100)*0.8) for i in scrsz]
            thisFig = plt.figure(figsize=fig_sz, dpi=100)

            # medians
            fig, ax = plt.subplot(2, 3, 0)
            ax.plot(preSA, preMedianResp(preSA), '*b')
            ax.plot(postOffset, postMedianResp(postSA), 'bo') # ,'markerfacecolor','b'
            #   ax.plot(pre, preMeanResp + preStdResp, '+g')
            #   ax.plot(post, postMeanResp + postStdResp, '+g')
            #   ax.plot(pre, preMeanResp - preStdResp, '+g')
            #   ax.plot(post, postMeanResp - postStdResp, '+g')
            ax.grid()

            # make the home EN of this plot red
            ax.plot(enInd, preMedianResp[enInd], 'ro')
            ax.plot(enInd + 0.25, postMedianResp[enInd], 'ro') # ,'markerfacecolor','r'
            ax.set(title=f'EN {enInd}\n median +/- std' )
            ax.set_xlim([0, max(preSA) + 1])
            ax.set_ylim([0, 1.1*max([ preMedianResp, postMedianResp ])])
            ax.set_xticks(preSA, minor=False)
            ax.set_xticklabels(trueXLabels)

            # connect pre to post with lines for clarity
            for j in range(len(preSA)):
                if j==1:
                    lineColor = 'r'
                else:
                    lineColor = 'b'
                ax.plot(
                        [preSA[j], postOffset[j]],
                        [preMedianResp[preSA[j]], postMedianResp[preSA[j]]],
                        lineColor
                        )

            # percent change in medians
            fig, ax = plt.subplot(2, 3, 1)
            ax.plot(
                preSA,
                (100*(postMedianResp[preSA] - preMedianResp[preSA]))/preMedianResp[preSA],
                'bo') # ,'markerfacecolor','b'
            # mark the trained odors in red:
            ax.plot(
                enInd,
                (100*(postMedianResp(enInd) - preMedianResp(enInd)))/preMedianResp[enInd],
                'ro') # ,'markerfacecolor','r'
            ax.set(title=r'% \Delta median')
            ax.set_xlim([0, max(preSA)+1])
            ax.set_ylim([-50,400])
            ax.set_xticks(preSA, minor=False)
            ax.set_xticklabels(trueXLabels)

            # relative changes in median, ie control/trained
            fig, ax = plt.subplot(2, 3, 2)

            y_vals = (pn *( (postMedianResp[preSA] - preMedianResp[preSA] )/preMedianResp[preSA] )) \
                / ( (postMedianResp[enInd] - preMedianResp[enInd] ) / preMedianResp[enInd] )
            ax.plot(preSA, y_vals, 'bo') # ,'markerfacecolor','b'
            # mark the trained odors in red
    #         plot(enInd, pn*1, 'ro','markerfacecolor','r')
    #         title(['relative ' del ' median'])
    #         xlim([0,max(preSA) + 1])
    #         % ylim([0,2])
    #         xticks(preSA)
    #         xticklabels(trueXLabels)
    #
    #         %------------------------------------------------------------------------
    #         % means
    #         % raw means, pre and post:
    #         subplot(2,3,4)
    #         hold on,
    #         grid on,
    #         errorbar(preSA, preMeanResp(preSA), preStdResp(preSA), 'bo')
    #         errorbar(postOffset, postMeanResp(postSA), postStdResp(postSA),'bo','markerfacecolor','b')
    #         errorbar(enInd, preMeanResp(enInd), preStdResp(enInd), 'ro')
    #         errorbar(enInd + 0.25, postMeanResp(enInd),  postStdResp(enInd), 'ro','markerfacecolor','r')
    #         title(['EN ' num2str(enInd), ' mean +/- std'])
    #         xlim([0,max(preSA) + 1])
    #         xticks(preSA)
    #         xticklabels(trueXLabels)
    #         ylim( [0  1.1*max([ preMeanResp, postMeanResp ]) + max([preStdResp, postStdResp]) ] )
    #
    #         % plot spont:
    #         errorbar(preSA(1), preHebMean, preHebStd,'mo')
    #         errorbar(postOffset(1), postHebMean, postHebStd,'mo','markerfacecolor','m')
    #
    #         % percent change in means
    #         subplot(2,3,5)
    #         hold on,
    #         grid on,
    #         plot(preSA, percentChangeInMeanResp,'bo','markerfacecolor','b')
    #         % mark the trained odors in red:
    #         plot(enInd, percentChangeInMeanResp(enInd),'ro','markerfacecolor','r')
    #         title([ '% ' del ' mean' ] )
    #         xlim([0,max(preSA) + 1])
    #         % ylim([-50,1000])
    #         xticks(preSA)
    #         xticklabels(trueXLabels)
    #
    #         % relative percent changes
    #         subplot(2,3,6)
    #         pn = sign( postMeanResp(enInd) - preMeanResp(enInd) );
    #         hold on,
    #         grid on,
    #         plot(preSA, pn*percentChangeInMeanResp  / percentChangeInMeanResp(enInd),'bo','markerfacecolor','b')
    #         % mark the trained odors in red:
    #         plot(enInd, pn*1, 'ro','markerfacecolor','r')
    #         title(['relative ' del ' mean' ])
    #         xlim([0,max(preSA) + 1])
    #         % ylim([0,2])
    #         xticks(preSA)
    #         xticklabels(trueXLabels)
    #
    #     end % if showPlots
    #  % Save plot code:
    #     if ~isempty(saveImageFolder) && showPlots(1)
    #         saveas( thisFig, fullfile(saveImageFolder,[resultsFilename '_en' num2str(enInd) '.png']), 'png')
    #     end
    #
    #     %---------------------------------------------------------------------------------
    #
    #     % store results in a struct:
    #     r(enInd).preTrainOdorResp = preTrainOdorResp;  % preserves all the sniffs for each stimulus
    #     r(enInd).postTrainOdorResp = postTrainOdorResp;
    #     r(enInd).preRespSniffsAved = preSA;   % the averaged sniffs for each stimulus
    #     r(enInd).postRespSniffsAved = postSA;
    #     r(enInd).odorClass = whichClass;
    #     r(enInd).percentChangeInMeanResp = percentChangeInMeanResp;  % key stat
    #     r(enInd).percentChangeInNoiseSubtractedMeanResp = percentChangeInNoiseSubtractedMeanResp;
    #     r(enInd).relativeChangeInNoiseSubtractedMeanResp = ...
    #         percentChangeInNoiseSubtractedMeanResp / percentChangeInNoiseSubtractedMeanResp(enInd);
    #     r(enInd).percentChangeInMedianResp = percentChangeInMedianResp;
    #     r(enInd).percentChangeInNoiseSubtractedMedianResp = percentChangeInNoiseSubtractedMedianResp;
    #     r(enInd).relativeChangeInNoiseSubtractedMedianResp = ...
    #         ( (postMedianResp - preMedianResp - postHebMean )./preMedianResp ) / ...
    #         ( (postMedianResp(enInd) - preMedianResp(enInd) - postHebMean )./preMedianResp(enInd) );
    #     r(enInd).trained = enInd;
    #     % EN odor responses, pre and post training.
    #     % these should be vectors of length numStims
    #     r(enInd).preMeanResp = preMeanResp;
    #     r(enInd).preStdResp = preStdResp;
    #     r(enInd).postMeanResp = postMeanResp;
    #     r(enInd).postStdResp = postStdResp;
    #     % spont responses, pre and post training:
    #     r(enInd).preSpontMean = mean(preSpont);
    #     r(enInd).preSpontStd = std(preSpont);
    #     r(enInd).postSpontMean = mean(postSpont);
    #     r(enInd).postSpontStd = std(postSpont);
    #
    #     results = r;
    #
    # end % for enInd = 1:numClasses
    #
    # %% Plot EN timecourses normalized by mean digit response:
    #
    # labels = whichClass;
    #
    # if showPlots(2)
    #     scrsz = get(0,'ScreenSize');
    #     % go through each EN:
    #     for enInd = 1:nE           % recal EN1 targets digit class 1, EN2 targets digit class 2, etc
    #         if mod(enInd - 1,3) == 0
    #             enFig2 = figure('Position',[scrsz(1), scrsz(2), scrsz(3)*1, scrsz(4)*1 ]); % make a new figure at ENs 4, 7, 10
    #         end
    #
    #         subplot(3, 1, mod(enInd - 1, 3) + 1 )
    #         hold on
    #
    #         xlim([-30, max(T)])
    #
    #         % plot octo
    #         plot( octoTimes, zeros(size(octoTimes)), 'yx')
    #
    #         % plot mean pre and post training of trained digit:
    #         preMean = r(enInd).preMeanResp;
    #         preMeanTr = preMean(enInd);
    #         preMeanControl = mean(preMean( [ 1:enInd-1, enInd+1:numClasses ]));
    #         preStd = r(enInd).preStdResp;
    #         preStd = preStd(enInd);
    #         postMean = r(enInd).postMeanResp;
    #         postMeanTr = postMean(enInd);
    #         postMeanControl = mean(postMean( [ 1:enInd-1, enInd+1:numClasses ]));
    #         postStd = r(enInd).postStdResp;
    #         postStd = postStd(enInd);
    #         preTime = T(T < startTrain);
    #         preTimeInds = find(T < startTrain);
    #         postTime = T(T > endTrain);
    #         postTimeInds = find(T > endTrain);
    #         midTime = T(T > startTrain & T < endTrain);
    #         midTimeInds = find(T > startTrain & T < endTrain);
    #
    #         % plot ENs:
    #
    #         plot( preTime, simRes['E'](preTimeInds,enInd)/preMeanControl , 'b');    % normalized by the home class preMean
    #         plot( postTime, simRes['E'](postTimeInds,enInd)/postMeanControl, 'b');    % normalized by the home class postMean
    #         plot( midTime, simRes['E'](midTimeInds, enInd)/ 1, 'b')
    #
    #         %             plot(preTime, preMean*ones(size(preTime)), 'color', colors{enInd},'lineStyle','-')
    #         %             plot(postTime, postMean*ones(size(postTime)), 'color', colors{enInd},'lineStyle','-')
    #         %             plot(preTime, (preMean-preStd)*ones(size(preTime)), 'color', colors{enInd},'lineStyle',':')
    #         %             plot(postTime, (postMean-postStd)*ones(size(postTime)), 'color', colors{enInd},'lineStyle',':')
    #         % plot stims by color
    #         for i = 1:numClasses
    #             plot( stimStarts(whichClass == classList(i)), zeros(size(stimStarts(whichClass == classList(i)))),...
    #                 'color', colors{i},'marker','.' ,'markersize',24, 'markerfacecolor', colors{i} ),
    #             % reinforce trained color:
    #             if i == enInd
    #                 plot( stimStarts(whichClass == classList(i)),...
    #                     0.001*ones(size(stimStarts(whichClass == classList(i)))),...
    #                     'color', colors{i},'marker','.' ,'markersize',24, 'markerfacecolor', colors{i} ),
    #             end
    #         end
    #
    #         set(gca,'fontname', 'Arial','fontweight','bold','fontsize',12)
    #         % format:
    #         ylim( [ 0, 1.2* max(simRes['E'](postTimeInds,enInd))/postMeanControl ] )
    #         rarrow = texlabel('/rarrow');
    #         title([ 'EN ' num2str(enInd) ' for class ' num2str( enInd ) ])
    #
    #  % Save EN timecourse:
    #         if ~isempty(saveImageFolder)  && (mod(enInd, 3) == 0 || enInd == 10)
    #             saveas( enFig2, fullfile(saveImageFolder,[resultsFilename '_enTimecourses' num2str(enInd) '.png']), 'png')
    #         end
    #
    #     end  % for enInd = 1:nE
    #
    # end % if showPlots

    return results
