import collections
from bokeh.plotting import figure, output_notebook, show, ColumnDataSource
from bokeh.models import HoverTool, BoxSelectTool, ResetTool
from bokeh.layouts import row, gridplot
from bokeh.palettes import Accent8 as cscheme
from bokeh.models import CheckboxGroup, CustomJS

output_notebook()

def plotting(feat1, feat2, playlists):
    '''Plot the two features feat1 & feat2 for all playlists in dictionary "playlists"

    Arguments
    --------
    feat1 = str, feature 1
    feat2 = str, feature 2
    playlists = dictionary of playlist names and song feature object returned by spotifyuser.get_song_features()

    Returns
    -------
    Bokeh plot with hover, reset and checkbox  ability.
    '''    
    hover = HoverTool(tooltips=[("Name", "@name"), ("Artist", "@artist")])
    
    q = figure(plot_width=600, plot_height=600, tools=[hover, ResetTool()],
            title="Feature Plot", x_axis_label =feat1, y_axis_label = feat2)
    
    dots = collections.OrderedDict()
    labels = []
    active = []
    counter = 0 
    for key in playlists:
        dots["scat_%02d"%counter] = q.circle(feat1, feat2, size=5, source=ColumnDataSource(playlists[key]), \
                                                color= cscheme[counter %8], legend = key, alpha = 1.0)
        labels.append(key)
        active.append(counter)
        counter +=1

    #Create code for checkbox
    code_block = "%s.visible = %s in checkbox.active;\
    "
    code = ""
    counter = 0
    for key in dots:
        code = code + (code_block%(key, str(counter)))
        counter +=1
    code = code + "show(checkbox.active)"
    
    #Create checkbox object
    checkbox = CheckboxGroup(labels=labels, active=active,  width=100)
    args = dots
    args["checkbox"] = checkbox
    checkbox.callback = CustomJS(args=args, lang="coffeescript", code=code)
    
    layout = row(q, checkbox)
    show(layout)
    


def plotting_flist(flist, feature_source):
    '''Plot the list of features for the given playlist

    Arguments
    --------
    flist = List of the features (atleast 2) to be plotted on scatter plot
    feature_source = Song feature object (Pandas data frame) returned by
    spotifyuser.get_song_features()
    
    Returns
    -------
    Bokeh grid plot showing with hover, brushing and reset ability.
    '''
    N = len(flist)
    
    if N >= 2:
        dim = N - 1
        size = int(800/dim)
        source = ColumnDataSource(feature_source)

        figs = []
        for foo in range(dim ):
            figs.append([None]*dim)
        for foo in range(dim):
            featx = flist[foo]
            for boo in range(foo +1, N):
                featy = flist[boo]
                hover = HoverTool(tooltips=[("Name", "@name"), ("Artist", "@artist")])
                figs[boo - 1][foo] = figure(plot_width=size, plot_height=size, 
                                            tools=[hover,BoxSelectTool(), ResetTool()],
                           title= featx + "-" + featy, x_axis_label =featx, y_axis_label = featy)
                figs[boo - 1][foo].circle(featx, featy, size=5, source=source, \
                                                        color= cscheme[5], alpha = 1.0)

        layout = gridplot(figs)
        show(layout)

    else:
        print("Need atleast 2 features")
