import sys, json

with open(sys.argv[1]) as f:
    data = json.load(f)

cal = data['data']['user']['contributionsCollection']['contributionCalendar']
total = cal['totalContributions']
weeks = cal['weeks']
max_count = max(
    (d['contributionCount'] for w in weeks for d in w['contributionDays']),
    default=0
)

CELL = 12
GAP = 3
OX = 40
OY = 30

def color(c):
    if c == 0: return '#161b22'
    if c <= 3: return '#0e4429'
    if c <= 7: return '#006d32'
    if c <= 15: return '#26a641'
    return '#39d353'

svg = '<svg xmlns="http://www.w3.org/2000/svg" width="740" height="180">'
svg += '<rect width="740" height="180" fill="#0d1117" rx="8"/>'
svg += f'<text x="20" y="22" font-family="system-ui,sans-serif" font-size="12" fill="#8b949e" font-weight="600">CONTRIBUTIONS</text>'
svg += f'<text x="20" y="44" font-family="system-ui,sans-serif" font-size="32" fill="#e6edf3" font-weight="700">{total}</text>'
svg += f'<text x="{22+len(str(total))*18}" y="44" font-family="system-ui,sans-serif" font-size="13" fill="#8b949e">in the last year</text>'

for wi, week in enumerate(weeks):
    for di, day in enumerate(week['contributionDays']):
        x = OX + wi * (CELL + GAP)
        y = OY + di * (CELL + GAP)
        c = color(day['contributionCount'])
        cnt = day['contributionCount']
        svg += f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{c}"><title>{day["date"]}: {cnt}</title></rect>'

months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
done = set()
for wi, week in enumerate(weeks):
    if week['contributionDays']:
        m = int(week['contributionDays'][0]['date'].split('-')[1])
        if m not in done:
            done.add(m)
            svg += f'<text x="{OX+wi*(CELL+GAP)}" y="{OY-8}" font-family="system-ui,sans-serif" font-size="9" fill="#8b949e">{months[m-1]}</text>'

for name, di in [('Mon',1),('Wed',3),('Fri',5)]:
    svg += f'<text x="5" y="{OY+di*(CELL+GAP)+9}" font-family="system-ui,sans-serif" font-size="8" fill="#8b949e">{name}</text>'

svg += '</svg>'

with open('/tmp/contributions.svg', 'w') as f:
    f.write(svg)
print(f'Generated: {total} total contributions, {len(weeks)} weeks')
