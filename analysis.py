import sys, json, pandas as pd, numpy as np
D, OUT = sys.argv[1], sys.argv[2]
o = pd.read_csv(f'{D}/orders.csv'); op = pd.read_csv(f'{D}/order_products_train.csv')
p = pd.read_csv(f'{D}/products.csv'); a = pd.read_csv(f'{D}/aisles.csv'); d = pd.read_csv(f'{D}/departments.csv')
R, T = {}, {}   # scalar results, tables
dow = {i:f'Day {i}' for i in range(7)}

pa = p.merge(a, on='aisle_id').merge(d, on='department_id')
opp = op.merge(pa, on='product_id')            # items with product info (drops ids missing from products)
R['n_orders_table']=len(o); R['n_items']=len(op); R['n_items_matched']=len(opp); R['n_orders_op']=op.order_id.nunique()
oj = op.merge(o, on='order_id')                # items whose order exists in orders table
R['n_orders_joined']=oj.order_id.nunique()

# Q1
T['Q1_top10_aisles_by_products'] = pa.groupby('aisle').size().sort_values(ascending=False).head(10).rename('products').reset_index()
# Q2
R['Q2_unique_departments']=int(p.department_id.nunique()); R['Q2_departments_table']=len(d)
# Q3
q3=pa.groupby('department').size().sort_values(ascending=False).rename('products').reset_index(); q3['pct']=(q3.products/q3.products.sum()*100).round(2)
T['Q3_products_by_department']=q3
# Q4
g=opp.groupby(['product_id','product_name']).reordered.agg(['mean','sum','count']).reset_index()
MIN=50
T['Q4_top10_reorder_rate']=g[g['count']>=MIN].sort_values(['mean','count'],ascending=False).head(10).rename(columns={'mean':'reorder_rate','sum':'reorders','count':'times_ordered'})
T['Q4_top10_reorder_rate']['reorder_rate']=T['Q4_top10_reorder_rate'].reorder_rate.round(4)
R['Q4_min_orders']=MIN
# Q5
R['Q5_unique_users']=int(o.user_id.nunique())
# Q6
u=o.groupby('user_id').days_since_prior_order.mean().rename('avg_days_between_orders').round(2).reset_index()
T['Q6_avg_days_per_user_ALL']=u
R['Q6_overall_mean']=float(u.avg_days_between_orders.mean()); R['Q6_median']=float(u.avg_days_between_orders.median())
R['Q6_users_with_value']=int(u.avg_days_between_orders.notna().sum())
T['Q6_summary']=u.avg_days_between_orders.describe().round(2).rename('value').reset_index()
T['Q6_user_avg_distribution']=pd.cut(u.avg_days_between_orders,[0,7,14,21,30],include_lowest=True).value_counts().sort_index().rename('users').reset_index().astype({'avg_days_between_orders':str})
# Q7/Q15
h=o.groupby('order_hour_of_day').size().rename('orders').reset_index(); h['pct']=(h.orders/h.orders.sum()*100).round(2)
T['Q7_Q15_orders_by_hour']=h
# Q8
w=o.groupby('order_dow').size().rename('orders').reset_index(); w['day']=w.order_dow.map(dow); w['pct']=(w.orders/w.orders.sum()*100).round(2)
T['Q8_orders_by_dow']=w[['order_dow','day','orders','pct']]
# Q9
T['Q9_top10_ordered_products']=opp.groupby('product_name').size().sort_values(ascending=False).head(10).rename('times_ordered').reset_index()
# Q10 (joined subset)
oj2=oj.merge(pa,on='product_id')
T['Q10_users_by_department']=oj2.groupby('department').user_id.nunique().sort_values(ascending=False).rename('unique_users').reset_index()
R['Q10_users_in_joined']=int(oj.user_id.nunique())
# Q11/Q14/Q16
sz=op.groupby('order_id').size()
R['Q11_avg_products_per_order_all']=float(sz.mean()); R['Q11_median']=float(sz.median())
szj=oj.groupby('order_id').size(); R['Q11_avg_products_per_order_joined']=float(szj.mean())
R['Q14_avg_cart_position']=float(op.add_to_cart_order.mean())
R['Q14_avg_max_cart_per_order']=float(op.groupby('order_id').add_to_cart_order.max().mean())
bins=[0,1,5,10,15,20,30,50,200]; lab=['1','2-5','6-10','11-15','16-20','21-30','31-50','51+']
bins=[0,1,5,10,15,20,30,50,1000]
T['Q16_order_size_distribution']=pd.cut(sz,bins).value_counts().sort_index().rename('orders').reset_index()
T['Q16_order_size_distribution']['size_band']=lab; T['Q16_order_size_distribution']['pct']=(T['Q16_order_size_distribution'].orders/len(sz)*100).round(2)
T['Q16_order_size_distribution']=T['Q16_order_size_distribution'][['size_band','orders','pct']]
R['Q16_max_order_size']=int(sz.max()); R['Q16_mode']=int(sz.mode()[0])
# Q12
pr=opp.groupby(['department','product_name']).reordered.sum().rename('reorders').reset_index()
T['Q12_top_reordered_per_dept']=pr.sort_values(['department','reorders'],ascending=[True,False]).groupby('department').head(1).sort_values('reorders',ascending=False).reset_index(drop=True)
# Q13
pc=opp.groupby('product_id').reordered.sum()
R['Q13_products_reordered_gt1']=int((pc>1).sum()); R['Q13_products_reordered_ge1']=int((pc>=1).sum()); R['Q13_products_ordered']=int(len(pc)); R['Q13_products_catalog']=len(p)
# Q17
q17=opp.groupby('aisle').reordered.agg(['mean','count']).rename(columns={'mean':'avg_reorder_rate','count':'items'}).sort_values('avg_reorder_rate',ascending=False).round(4).reset_index()
T['Q17_reorder_rate_by_aisle']=q17
# Q18 (joined subset)
q18=oj.groupby('order_id').agg(size=('product_id','size'),dow=('order_dow','first')).groupby('dow')['size'].agg(['mean','count']).round(2).reset_index()
q18['day']=q18.dow.map(dow); q18.columns=['order_dow','avg_order_size','orders','day']; T['Q18_avg_order_size_by_dow']=q18[['order_dow','day','avg_order_size','orders']]
# Q19
q19=o.groupby('user_id').agg(orders_in_data=('order_id','size'),max_order_number=('order_number','max')).sort_values(['orders_in_data','max_order_number'],ascending=False).head(10).reset_index()
T['Q19_top10_users_by_orders']=q19
# Q20
T['Q20_products_per_aisle_dept']=pa.groupby(['department','aisle']).size().rename('products').reset_index().sort_values(['department','products'],ascending=[True,False])
# extra behaviour
dep_rr=opp.groupby('department').reordered.agg(['mean','count']).round(4).sort_values('mean',ascending=False).rename(columns={'mean':'reorder_rate','count':'items'}).reset_index()
T['X_reorder_rate_by_department']=dep_rr
cp=op.assign(pos=pd.cut(op.add_to_cart_order,[0,1,2,3,5,10,20,200],labels=['1','2','3','4-5','6-10','11-20','21+'])).groupby('pos',observed=True).reordered.mean().round(4).rename('reorder_rate').reset_index()
T['X_reorder_rate_by_cart_position']=cp
dsp=o.days_since_prior_order.value_counts().sort_index().rename('orders').reset_index(); T['X_days_since_prior_dist']=dsp
R['X_overall_reorder_rate']=float(op.reordered.mean())
R['X_pct_orders_on_30d']=float((o.days_since_prior_order==30).mean()*100); R['X_pct_orders_7d']=float((o.days_since_prior_order==7).mean()*100)
R['X_pct_orders_within_7d']=float((o.days_since_prior_order<=7).mean()*100)
R['X_first_orders_pct']=float(o.days_since_prior_order.isna().mean()*100)
R['X_orders_per_user_mean']=float(o.groupby('user_id').size().mean())
R['Q19_users_at_100']=int((o.groupby('user_id').size()==100).sum())
# hour x dow heatmap
hm=o.pivot_table(index='order_dow',columns='order_hour_of_day',values='order_id',aggfunc='count'); T['X_hour_dow_heatmap']=hm.rename(index=dow).reset_index()
# department share of items
T['X_dept_item_share']=(opp.groupby('department').size().sort_values(ascending=False)/len(opp)*100).round(2).rename('pct_of_items').reset_index()
# top aisles by volume
T['X_top_aisles_by_items']=opp.groupby('aisle').size().sort_values(ascending=False).head(10).rename('items').reset_index()
# reorder rate per dow/hour (joined)
T['X_reorder_by_dow']=oj.groupby('order_dow').reordered.mean().round(4).rename('reorder_rate').reset_index().assign(day=lambda x:x.order_dow.map(dow))
# basket: size vs reorder
for k,v in T.items(): pass
import pickle; pickle.dump((R,T),open(f'{OUT}/results.pkl','wb'))
with pd.ExcelWriter(f'{OUT}/Market_Analysis_Results.xlsx') as xw:
    for k,v in T.items():
        v.to_excel(xw,sheet_name=k[:31],index=False)
    pd.Series(R).rename('value').to_frame().to_excel(xw,sheet_name='Scalars')
print(json.dumps(R,indent=1,default=float))
for k,v in T.items():
    if k in('Q6_avg_days_per_user_ALL','Q20_products_per_aisle_dept','X_days_since_prior_dist','Q17_reorder_rate_by_aisle'): continue
    print('\n##',k); print(v.head(25).to_string(index=False))
