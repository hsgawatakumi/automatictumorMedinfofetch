#!/usr/bin/env python3
from src.database import init_database

db = init_database('data/medical_info.db')
print('=== CDE数据 ===')
cde = db.execute_query("SELECT trial_id, study_title_cn, trial_status, url FROM clinical_trials WHERE platform='CDE' LIMIT 10")
for t in cde:
    print(t)
print()
print('=== ChiCTR数据 ===')
chictr = db.execute_query("SELECT trial_id, study_title_cn, trial_status, url FROM clinical_trials WHERE platform='ChiCTR' LIMIT 10")
for t in chictr:
    print(t)
db.close()