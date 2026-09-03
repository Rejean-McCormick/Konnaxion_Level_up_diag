PASS="PASS"; WARN="WARN"; FAIL="FAIL"; SKIP="SKIP"; BLOCKED="BLOCKED"; PARTIAL="PARTIAL"; ERROR="ERROR"; INFRA_ERROR="INFRA_ERROR"; CONFIG_ERROR="CONFIG_ERROR"
VERDICTS=(PASS,WARN,FAIL,SKIP,BLOCKED,PARTIAL,ERROR,INFRA_ERROR,CONFIG_ERROR)
_RANK={PASS:0,SKIP:0,WARN:1,PARTIAL:2,BLOCKED:3,INFRA_ERROR:4,FAIL:5,ERROR:6,CONFIG_ERROR:7}

def aggregate_verdicts(values):
    vals=[v for v in values if v in _RANK]
    return max(vals,key=lambda x:_RANK[x]) if vals else PASS

def exit_code(verdict):
    if verdict in {PASS,WARN,SKIP}: return 0
    if verdict==FAIL: return 10
    if verdict in {PARTIAL,BLOCKED}: return 20
    return 30
