#!/usr/bin/env python2

import argparse

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.patches as patches
import numpy as np

import melo_sr as melo
import srdb


# figure style
plt.style.use('fivethirtyeight')

# figure size
aspect = 1/1.618
resolution = 72.27
columnwidth = 180/resolution
textwidth = 373/resolution
textheight = 672/resolution
textiny, texsmall, texnormal = 7.9, 9.25, 10.0
offblack = '#333333'
blue = '#1b6394'
orange = '#F1A107'

plt.rcParams.update({
    'font.size': texsmall,
    'legend.fontsize': texsmall,
    'axes.labelsize': texsmall,
    'axes.titlesize': texsmall,
    'xtick.labelsize': textiny,
    'ytick.labelsize': textiny,
    'font.weight': 400,
    'axes.labelweight': 400,
    'axes.titleweight': 400,
    'lines.linewidth': .9,
    'lines.markersize': 3,
    'lines.markeredgewidth': .1,
    'patch.linewidth': .9,
    'axes.linewidth': .5,
    'xtick.major.width': .5,
    'ytick.major.width': .5,
    'xtick.minor.width': .5,
    'ytick.minor.width': .5,
    'xtick.major.size': 2,
    'ytick.major.size': 2,
    'xtick.minor.size': 1.3,
    'ytick.minor.size': 1.3,
    'xtick.major.pad': 1.8,
    'ytick.major.pad': 1.8,
    'text.color': offblack,
    'axes.labelcolor': offblack,
    'xtick.color': offblack,
    'ytick.color': offblack,
    'legend.numpoints': 1,
    'legend.scatterpoints': 1,
    'legend.frameon': False,
    'image.interpolation': 'none',
    'pdf.fonttype': 3,
})


plot_functions = {}


def plot(f):
    def wrapper(*args, **kwargs):
        print(f.__name__)
        f(*args, **kwargs)
        plt.savefig('{}.png'.format(f.__name__), dpi=150)
        plt.close()

    plot_functions[f.__name__] = wrapper

    return wrapper


def finish(despine=True, remove_ticks=False, pad=0.1,
           h_pad=None, w_pad=None, rect=[0, 0, 1, 1]):
    fig = plt.gcf()

    for ax in fig.axes:
        if despine:
            for spine in 'top', 'right':
                ax.spines[spine].set_visible(False)

        if remove_ticks:
            for ax_name in 'xaxis', 'yaxis':
                getattr(ax, ax_name).set_ticks_position('none')
        else:
            ax.xaxis.set_ticks_position('bottom')
            ax.yaxis.set_ticks_position('left')

    fig.tight_layout(pad=pad, h_pad=h_pad, w_pad=w_pad, rect=rect)

@plot
def ratings(year, week):
    """
    Offensive and deffensive power ratings for each team

    """
    plt.figure(figsize=(3.8, 4))

    #q = nfldb.Query(nfldb.connect())
    #q.game(season_type='Regular', season_year=year, week=week)

    spread_rtg, total_rtg = [
            melo.Rating(mode=mode, database='elo.db')
            for mode in ('spread', 'total')
            ]

    spreads, totals = [[
        rtg.predict_score(team, 'AVG', year, week) for team in rtg.teams
        ] for rtg in (spread_rtg, total_rtg)
        ]
    
    smin, smax = min(spreads), max(spreads)
    colors = [plt.cm.coolwarm((s - smin)/(smax - smin)) for s in spreads]

    for team, spread, total, color in zip(
            spread_rtg.teams, spreads, totals, colors):

        offense = 0.5*(total + spread)
        defense = 0.5*(total - spread)

        bump = .05
        plt.scatter(defense, offense, c=color, s=15,
                    edgecolor=offblack, linewidth=.4)
        plt.annotate(team, xy=(defense - bump, offense + bump),
                     xycoords='data', ha='left')

    ax = plt.gca()
    #ax.set_aspect('equal')

    for axis in ax.xaxis, ax.yaxis:
        loc = ticker.MultipleLocator(base=1)
        axis.set_major_locator(loc)

    ax.grid(True, which='both')
    ax.invert_xaxis()

    plt.xlim(29, 17)
    plt.ylim(17, 29)
    plt.xlabel('Points Allowed')
    plt.ylabel('Points Scored')
    plt.title('Season {}, Week {}'.format(year, week))
    finish(pad=.5)


def points(mode, year=2017, week=1):
    """
    This function predicts the point total and point spread
    for a specified year and week using the margin-dependent
    Elo  model.

    """
    plt.figure(figsize=(columnwidth, columnwidth/aspect))
    ax = plt.gca()

    #q = nfldb.Query(nfldb.connect())
    #q.game(season_type='Regular', season_year=year, week=week)

    rating = melo.Rating(mode=mode, database='elo.db')

    xlim = {'spread': (-37, 37), 'total': (5, 85)}
    xticks = {'spread': np.linspace(-30, 30, 7),
              'total': np.linspace(15, 75, 5)}
    xlabel = {'spread': r'$\mathrm{home} - \mathrm{away}$ [points]',
              'total': r'$\mathrm{home} + \mathrm{away}$ [points]'}

    xmin, xmax = xlim[mode]

    # loop over games in the week
    for shift, game in enumerate(srdb.games, start=1):

        home, away = (game.home_team, game.away_team)

        median = rating.predict_spread(home, away, year, week)
        mean = rating.predict_score(home, away, year, week)
        int_median = int(round(median))

        box1, box2 = [
                rating.predict_spread(home, away, year, week, perc=p)
                for p in (.25, .75)
                ]

        box_lo, box_hi = (min(box1, box2), max(box1, box2))

        line1, line2 = [
                rating.predict_spread(home, away, year, week, perc=p)
                for p in (.05, .95)
                ]

        line_lo, line_hi = (min(line1, line2), max(line1, line2))

        box = patches.Rectangle(
                (box_lo, shift-.15), box_hi - box_lo, 0.3,
                color=blue, alpha=.8, lw=0
                )

        ax.add_patch(box)

        plt.plot((line_lo, box_lo), (shift, shift),
                 color=blue, alpha=.8, lw=1.2)

        plt.plot((box_hi, line_hi), (shift, shift),
                 color=blue, alpha=.8, lw=1.2)

        plt.plot((median, median), (shift-.15, shift+.15),
                 color=orange, lw=1.2)

        plt.scatter(mean, shift, color=orange, zorder=4)

        for team, xloc in (home, xmax), (away, xmin):
            plt.annotate(team, xy=(xloc, shift), clip_on=False,
                         xycoords='data', ha='center', va='center')

        plt.annotate(int_median, xy=(median, shift+.4), clip_on=False,
                     xycoords='data', ha='center', va='center', fontsize=9)

    for team, xfrac in ('AWAY', 0), ('HOME', 1):
        plt.annotate(team, xy=(xfrac, 1.02), xycoords='axes fraction',
                     clip_on=False, ha='center', va='center', color='.7')

    plt.xlim(xmin, xmax)
    plt.xticks(xticks[mode])
    plt.xlabel(xlabel[mode])

    plt.ylim(.5, shift + .5)
    plt.yticks([])

    finish(rect=(0.07, 0, 0.93, 0.97))


@plot
def spreads(year, week):
    points('spread', year, week)


@plot
def totals(year, week):
    points('total', year, week)


def main():
    """
    Calculates the point spread and point total distributions for
    the specified season year and week.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "year",
            action="store",
            type=int,
            help="NFL season year (2009-present)"
            )
    parser.add_argument(
            "week",
            action="store",
            type=int,
            help="NFL week (1-17)"
            )

    args = parser.parse_args()
    args_dict = vars(args)

    # plot offensive and defensive ratings
    ratings(**args_dict)

    # plot the point spread and point total
    for plot in spreads, totals:
        plot(**args_dict)


if __name__ == "__main__":
    main()
