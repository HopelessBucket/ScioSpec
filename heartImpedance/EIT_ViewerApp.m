classdef EIT_ViewerApp < matlab.apps.AppBase
    % EIT_ViewerApp  ‑  Minimal‑GUI für Echtzeit‑Simulation
    % --------------------------------------------------------------
    % · Lädt ein measurement‑Table aus einer .mat‑Datei
    % · Spielt die Zeilen in Echtzeit (Timer) ab
    % · Plottet |Z| oder |Y| + Phase gegen Zeitindex
    % --------------------------------------------------------------

    properties (Access = public)
        UIFigure      matlab.ui.Figure
        LoadButton    matlab.ui.control.Button
        StartButton   matlab.ui.control.Button
        ZYDropDown    matlab.ui.control.DropDown
        FreqDropDown  matlab.ui.control.DropDown
        MagAxes       matlab.ui.control.UIAxes
        PhaseAxes     matlab.ui.control.UIAxes
    end

    properties (Access = private)
        simData table       % measurement‑Table
        simPtr  double = 1  % aktueller Zeiger
        tmr     timer       % Timer‑Objekt
    end

    properties (Constant, Access = private)
        TIMER_PERIOD = 0.3; % Sekunden pro Schritt
    end

    %==================================================================
    % Konstruktor
    %==================================================================
    methods (Access = public)
        function app = EIT_ViewerApp
            createComponents(app);
            registerCallbacks(app);
        end
    end

    %==================================================================
    % GUI‑Aufbau
    %==================================================================
    methods (Access = private)
        function createComponents(app)
            app.UIFigure = uifigure('Name','EIT Viewer','Position',[100 100 900 550]);
            gl = uigridlayout(app.UIFigure,[3 5]);
            gl.RowHeight   = {35 35 '1x'};
            gl.ColumnWidth = {100 120 120 120 '1x'};

            % Buttons
            app.LoadButton  = uibutton(gl,'Text','Load .mat','ButtonPushedFcn',@(s,e)onLoad(app));
            app.StartButton = uibutton(gl,'Text','Start','Enable','off','ButtonPushedFcn',@(s,e)onStart(app));
            app.LoadButton.Layout.Column  = 1; app.LoadButton.Layout.Row  = 1;
            app.StartButton.Layout.Column = 2; app.StartButton.Layout.Row = 1;

            % DropDowns
            app.ZYDropDown   = uidropdown(gl,'Items',{'Impedance Z','Admittance Y'},'ValueChangedFcn',@(s,e)updatePlots(app));
            app.FreqDropDown = uidropdown(gl,'Items',{'‑'},'ValueChangedFcn',@(s,e)updatePlots(app));
            app.ZYDropDown.Layout.Column   = 1; app.ZYDropDown.Layout.Row   = 2;
            app.FreqDropDown.Layout.Column = 2; app.FreqDropDown.Layout.Row = 2;

            % Achsen
            axGrid = uigridlayout(gl,[1 2]);
            axGrid.Layout.Row = 3; axGrid.Layout.Column = [1 5];
            app.MagAxes   = uiaxes(axGrid); title(app.MagAxes,'|Z| / |Y|');
            app.PhaseAxes = uiaxes(axGrid); title(app.PhaseAxes,'Phase [°]');
            linkaxes([app.MagAxes app.PhaseAxes],'x');
        end

        function registerCallbacks(~)
            % callbacks bereits gesetzt in createComponents
        end
    end

    %==================================================================
    % Button‑Callbacks
    %==================================================================
    methods (Access = private)
        function onLoad(app)
            [f,p] = uigetfile('*.mat','Measurement .mat wählen');
            if f==0, return, end
            S = load(fullfile(p,f));
            if ~isfield(S,'measurement')
                uialert(app.UIFigure,'Datei enthält kein ''measurement''‑Table.','Fehler'); return
            end
            app.simData = S.measurement;
            % Dropdowns befüllen
            freqs = unique(app.simData.Frequency);
            app.FreqDropDown.Items = cellstr(num2str(freqs));
            app.StartButton.Enable = 'on';
            app.simPtr = 1;
            cla(app.MagAxes); cla(app.PhaseAxes);
        end

        function onStart(app)
            if isempty(app.simData), return, end
            app.StartButton.Enable = 'off';
            app.tmr = timer('ExecutionMode','fixedSpacing','Period',app.TIMER_PERIOD, ...
                'TimerFcn',@(~,~)timerStep(app));
            start(app.tmr);
        end
    end

    %==================================================================
    % Timer‑und Plot‑Logik
    %==================================================================
    methods (Access = private)
        function timerStep(app)
            if app.simPtr > height(app.simData)
                stop(app.tmr); delete(app.tmr); app.StartButton.Enable='on'; return
            end
            newRow = app.simData(app.simPtr,:); app.simPtr = app.simPtr + 1;
            % Anhängen und Plot aktualisieren
            if app.simPtr==2
                app.simDataPlt = newRow;
            else
                app.simDataPlt(end+1,:) = newRow; %#ok<AGROW>
            end
            updatePlots(app);
        end

        function updatePlots(app)
            if ~isprop(app,'simDataPlt') || isempty(app.simDataPlt), return, end
            df = app.simDataPlt;
            % Frequenzfilter
            selF = str2double(app.FreqDropDown.Value);
            if ~isnan(selF)
                df = df(df.Frequency==selF,:);
            end
            % Z oder Y
            Z = df.Impedance;
            if startsWith(app.ZYDropDown.Value,'Admittance')
                Z = 1./Z;
            end
            t = (1:height(df))';
            cla(app.MagAxes); cla(app.PhaseAxes);
            plot(app.MagAxes,t,abs(Z),'o-');
            plot(app.PhaseAxes,t,rad2deg(angle(Z)),'x-');
            xlabel(app.PhaseAxes,'Sample #');
            drawnow limitrate;
        end
    end
end
