''' Generates a graph showing Github team contributions for specified team(s) and
# date range.'''
import os
import time
import calendar
from datetime import datetime, timezone, date, timedelta
import matplotlib.pyplot as plt
import matplotlib.patheffects as PathEffects
import pandas as pd
from github import Github

def api_wait_search(git, min_srchs=4):
    ''' Automatic rate limiter '''
    limits = git.get_rate_limit()
    if limits.search.remaining <= min_srchs:
        local_reset = limits.search.reset.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        seconds = round((local_reset - now).total_seconds()) + 20 # add 20 secs as GH isn't precise
        print(f'API rate limit exceeded - waiting for {seconds} seconds...')
        time.sleep(seconds)
        print("Done waiting - resuming.")

def get_AC_team(git, targets='triage'):
    ''' Given a team designation, return names of all members'''
    # AC ID = 20147732, Bug Triaging Team ID = 4914022, Senior BT = 4916549
    # testers = 2167099, devs = 2059572
    # Multiple teams can be merged and treated as one unit, i.e. triage/senior triage
    # Can also manually specify team members, as for paiddevs team, where no
    # formal team in Github exists.
    teamnames = []
    org = git.get_organization('azerothcore')
    id_dict = {'triage': [4914022, 4916549], 'alldevs': [2059572],
                'testers': [2167099]}

    if targets in id_dict.keys():
        team_ids = id_dict[targets]
    else: # no team id, directly specify team names instead
        teamnames = ['UltraNix', 'IntelligentQuantum', 'Nyeriah', 'Nefertumm',
                     'Winfidonarleyan']
        team_ids = []

    for team_id in team_ids:
        team = org.get_team(team_id)
        # just gets first page of names, no team is larger than that so isn't a problem
        teamlist = team.get_members().get_page(0)
        teamnames += [x.login for x in teamlist]
    return sorted(list(set(teamnames)), key = lambda x:x.capitalize(), reverse=True)

def convert_data(data, targets):
    newdata = {'Name':list(data.keys())}

    if targets == 'triage':
        headings = ['AC Issues Created', 'CC Issues Involved', 'PRs Created'] # 'AC Other',
    elif targets in ['paiddevs', 'alldevs']:
        headings = ['PRs Made', 'PRs Reviewed']
    elif targets == 'testers':
        headings = ['PRs Involved', 'PRs Made']

    for num, k in enumerate(headings):
        newdata[k] = [x[num] for x in data.values()]
    return newdata

def generate_stackbar(data, targets, datemode, datevar):
    titles = {'triage': 'Triaging Team', 'testers': 'Testing Team',
              'paiddevs': 'Hired Developers', 'alldevs': 'All Developers'}
    data = convert_data(data, targets)
    df = pd.DataFrame(data)
    df.set_index('Name', inplace=True)

    graphtitles = {'daysback': f'Last {datevar} Days',
                   'year': f'Year {datevar}',
                   'month': f'{calendar.month_name[datevar] if 1 <= datevar <= 12 else "x"}'}
    graphtitle = f'AC {titles[targets]} Activity For ' + graphtitles[datemode]
    filename = graphtitle + f' - {date.today().isoformat()}.png'

    font_color = 'black'
    hfont = {'fontname':'Calibri'}

    ax = df.plot(kind='barh', stacked=True, edgecolor='black', linewidth=1,
    width=0.75, figsize=(12, 7.5), color=[u'#1f77b4', u'#2ca02c', u'#d62728'])

    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontsize(16)
        plt.xticks(color=font_color, **hfont)
        plt.yticks(color=font_color, **hfont)

    for p in ax.patches:
        width, height = p.get_width(), p.get_height()
        x, y = p.get_xy()
        if width:
            text = ax.text(x+width/2, y+height/2, '{:.0f}'.format(width),
                horizontalalignment='center', verticalalignment='center',
                color='white', fontsize=18, **hfont)
            text.set_path_effects([PathEffects.withStroke(linewidth=2, foreground='black')])

    title = plt.title(f'{graphtitle}', fontsize=16, color=font_color, **hfont)
    ax.legend()
    plt.tight_layout()
    plt.savefig(f'{filename}', dpi=100)
    plt.show()

def generate_searchstrs(contrib, datemode='daysback', datevar=30, targets='triage'):
    lastdays = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    srchstrs = []
    curryear = time.localtime()[0]

    if datemode == 'daysback':
        days_before = (date.today() - timedelta(days=datevar)).isoformat()
        datestr = f'created:>={days_before}'
    elif datemode == 'month':
        lastday = lastdays[datevar]
        monthvar = str(datevar).zfill(2)
        datestr = f'created:{curryear}-{monthvar}-01..{curryear}-{monthvar}-{lastday}'
    elif datemode == 'year':
        datestr = f'created:{datevar}-01-01..{datevar}-12-31'

    if targets == 'triage':
        srchstrs = [f'is:issue {datestr} author:{contrib} org:azerothcore',
                    f'is:issue {datestr} involves:{contrib} repo:chromiecraft/chromiecraft',
                    f'is:pr {datestr} org:azerothcore author:{contrib}',
                    f'is:issue {datestr} author:{contrib} repo:chromiecraft/chromiecraft']
    elif targets in ['paiddevs', 'alldevs']:
        srchstrs = [f'is:pr {datestr} org:azerothcore author:{contrib}',
                    f'is:pr {datestr} org:azerothcore reviewed-by:{contrib}']
    elif targets == 'testers': # not really useful as performance metrics, ask Temper
        srchstrs = [f'is:pr {datestr} involves:{contrib} org:azerothcore',
                    f'is:pr {datestr} author:{contrib} org:azerothcore']
    return srchstrs

def scan_contribs(git, targets='triage', datemode='daysback', datevar=30):
    '''Given a team designation and a date range, retrieve stats for team members'''
    teamlist = get_AC_team(git, targets)
    cont_data = {k:[] for k in teamlist}

    for contrib in teamlist:
        print(f'Scanning contributions for {contrib}...')
        srchstrs = generate_searchstrs(contrib, datemode, datevar, targets)
        api_wait_search(git, len(srchstrs))
        for srch in srchstrs:
            results = git.search_issues(srch)
            cont_data[contrib].append(results.totalCount)
        time.sleep(4)

    if targets == 'triage': # subtract authored CC issues from involved issues
        for k, v in cont_data.items():
            cont_data[k] = [v[0], max(v[1] - v[3], 0), v[2]]

    if targets == 'testers': # subtract authored AC PRs from involved PRs
        for k, v in cont_data.items():
            cont_data[k] = [v[0] - v[1], v[1]]

    if targets != 'paiddevs': # remove null contributors from all but paiddevs
        cont_data = {k:v for k, v in cont_data.items() if sum([1 for x in v if not x]) != len(v)}

    totals = []
    for p in range(len(list(cont_data.values())[0])):
        totals.append(sum([v[p] for v in cont_data.values()]))
    if targets == 'triage':
        print(f'AC total created: {totals[0]}, CC involved: '\
              f'{totals[1]}, PRs made: {totals[2]}.')
    elif targets in ['paiddevs', 'alldevs']:
        print(f'PRs made: {totals[0]}, PRs reviewed: {totals[1]}')

    # can clear a specified team member's stats here
    #if 'Azcobu' in cont_data:
        #del cont_data['Azcobu']

    print(cont_data)
    return cont_data

def main():
    # Time modes: daysback = last X days, month = activity in the listed month of this year,
    #             year = activity for that year. If not specified, defaults to daysback.
    datemode = 'month'
    # datevar: if time mode is dayback, datevar is number of days to go back. (default = 30)
    #          if time mode is month, datevar is number of month, i.e. May = 5
    #          if time mode is year, datevar is the year.
    datevar = 11
    # Targets: which team or people to gather stats on.
    # Options are 'triage', 'paiddevs', 'alldevs', 'testers'. Default is triage.
    targets = 'paiddevs'

    if token := os.getenv('GITHUB_TOKEN'):
        data = scan_contribs(Github(token), targets, datemode, datevar)
        generate_stackbar(data, targets, datemode, datevar)

if __name__ == '__main__':
    main()
