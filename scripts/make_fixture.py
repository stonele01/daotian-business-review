"""Create a synthetic workbook for end-to-end mapping tests; never reads company data."""
import argparse
import json
from pathlib import Path
from openpyxl import Workbook


def create(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    d=json.loads((Path(__file__).resolve().parent.parent/'examples/demo.json').read_text('utf-8'))
    wb=Workbook();a=wb.active;a.title='经营';b=wb.create_sheet('渠道')
    a.append(['账号','本期总额','上期总额','本期自营','上期自营','本期消耗','上期消耗','代理商'])
    b.append(['账号','本期总额','上期总额','本期短视频','上期短视频','本期直播','上期直播','本期商品卡','上期商品卡'])
    for i,r in enumerate(d['accounts']):
        a.append([r['name'],r['total']['current'],r['total']['prior'],r['self']['current'],r['self']['prior'],r['spend']['current'],r['spend']['prior'],r['agency']])
        b.append(['示例青禾别名' if i==0 else r['name'],r['total']['current'],r['total']['prior']]+[c[p] for c in r['channels'] for p in ('current','prior')])
    a.append(['合计',sum(r['total']['current'] for r in d['accounts']),sum(r['total']['prior'] for r in d['accounts'])])
    for ws in wb:
        ws.freeze_panes='B2'
        for key in 'ABCDEFGHI':ws.column_dimensions[key].width=20
    wb.save(out/'source.xlsx')
    return out/'source.xlsx'


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True)
    print(create(p.parse_args().out))
