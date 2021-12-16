## github-teamactivity

This is a simple utility to gather and graph statistics about team activity on Github. It's currently setup to track activity for various AzerothCore project teams, but can be used to track any team or combination of teams on Github if you know their IDs. Configuration is by editing the code directly, as it's too small to worry about more proper means. 

#### Requirements

- To access the Github API, you need a personal access token - details here: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token
- You can import the token into the code however you like - for this I'm using an OS environment variable called 'GITHUB_TOKEN' to store it. For security reasons this is preferable to just hard-coding the token in your code.

#### Useage

The major variables are:
- 'targets' - which team we're gathering statistics for. Has the options 'triage', 'selectdevs', 'alldevs', and 'testers'. These designations map onto one or more Github team IDs except for 'selectdevs' which is intended to allowed custom groupings. (So for example 'triage' merges members of two teams, Bug Triaging and Senior Bug Triaging.) To find a Github team ID, see https://fabian-kostadinov.github.io/2015/01/16/how-to-find-a-github-team-id/ 
- 'datemode' - the time period we're looking at. Options are 'daysback' (last X days from today), 'month', or 'year'.

#### Other Notes
- The metrics are for the entire AC organization, rather than just the one main repo. So editing the AC wiki counts as making a PR, for example. 
- Some totals are adjusted to remove activity that we don't want to track. For example, the "CC Involved" metric for triagers counts all Chromie issues that the triager interacted with in some way. However, this was also counting CC issues created by that triager, which we're not interested in, so the CC issues authored total is subtracted from the CC issues involved total to get the actual number of issues a triager worked on. 
- The metrics don't work very well for testers. Temper and I had a talk about this and there's not really a fair way to count these using Github stats.

#### Examples

Alldevs/Daysback/7:

![Alldevs/Daysback/7](AC%20All%20Developers%20Activity%20For%20Last%207%20Days%20-%202021-12-11.png)

Selectdevs/Month/11

![Selectdevs/Month/11](AC%20Selected%20Developers%20Activity%20For%20November%20-%202021-12-11.png)

Triage/Year/2021

![Triage/Year/2021](AC%20Triaging%20Team%20Activity%20For%20Year%202021%20-%202021-12-11.png)

