from flask import Flask, jsonify, request,abort,g, render_template
import sqlite3
from datetime import datetime, timedelta
import re

app = Flask(__name__)

@app.route('/')
def blank():
    return app.send_static_file('index.html')

def opendbconn():
    conn = sqlite3.connect('CheeseWatch.db')
    return conn

@app.route('/api/lastupdate')
def last_update():
    conn = opendbconn()
    enddate = conn.execute('select obsdate from observations order by obsdate desc limit 1').fetchone()
    return str(enddate[0])



@app.route('/api/scannames')
def get_scannames():
    conn = opendbconn()

    scannames = []
    for row in conn.execute('select distinct scanname from urls'):
        scannames.append(row[0])
    conn.close()
    return jsonify(scannames)

@app.route('/api/products', methods=['POST','GET'])
def get_products():
    try:
        scanname = request.args.get('scanname','').lower()
        print('Got scan name '+ scanname)
    except KeyError as e:
        abort(404)
    
    conn = opendbconn()
    enddate=last_update()
    products = []

    for row in conn.execute('select distinct(productid), productname,scanname,obsprice from observations where obsdate=? and scanname like?',[enddate,scanname]):
        products.append(row)
    conn.close()
    return jsonify(products)

@app.route('/api/pricehistory',methods=['GET'])
def get_pricehistory():
    try:
        productid = request.args.get('productid')
    except KeyError as e:
        abort(404)
    if productid==None:
        abort(404)

    enddate=request.args.get('enddate',default='today')
    print('enddate: ' + enddate)
    if enddate=='today':
        enddate=last_update()
    startdate = request.args.get('startdate',default='2022-12-01')
    print('start date: '+ startdate)

    conn = opendbconn()

    pricehistory = conn.execute('select productid, obsdate, obsprice,promobadgeimagelabel from observations \
        where productid like ? and obsdate>=? and obsdate<=?',[productid+'%', startdate, enddate],).fetchall()
    conn.close()

    if len(pricehistory)==0:
        print('No history')
        return 'Error No history found'
        
    prices = []
    x = []
    y = []
    promo = []
    csv = 'date,price,promo\n'
    
    for row in pricehistory:
        x.append(row[1])
        y.append(row[2])
        promo.append(row[3])
        
        csv = csv + f'{row[1]}, {row[2]}, {row[3]} \n'

    return csv

@app.route('/api/categoryhistory',methods=['GET'])
def get_categoryhistory():
    catname = request.args.get('category', default=None)
    if catname==None:
        abort(404)

    conn = opendbconn()

    pricehistory = conn.execute('select productname, obsdate, obsprice, promobadgeimagelabel from observations \
        where scanname like ? and obsdate>=? and obsdate<=? order by obsdate asc',[catname+'%', startdate, enddate],).fetchall()
    conn.close()

    if len(pricehistory)==0:
        print('No history')
        return 'Error No history found'
        
    prices = []
    x = []
    y = []
    promo = []
    csv = 'date,price,promo\n'

    
    for row in pricehistory:
        x.append(row[1])
        y.append(row[2])
        promo.append(row[3])
        
        csv = csv + f'{row[1]}, {row[2]}, {row[3]} \n'

    return csv
    
@app.route('/pricechanges')
def pricechanges():
    enddate=request.args.get('enddate',default='today')
    lastupdate = last_update()
    if enddate=='today':
        enddate=lastupdate
    
    dttoday = datetime.strptime(enddate,'%Y-%m-%d')
    dtyesterday = dttoday-timedelta(days=1)
    yesterday = dtyesterday.strftime('%Y-%m-%d')
    dtlastweek = dttoday - timedelta(days=7)
    lastweek = dtlastweek.strftime('%Y-%m-%d')
    dtlastmonth = dttoday - timedelta(days=30)
    lastmonth = dtlastmonth.strftime('%Y-%m-%d')
    

    startdate = request.args.get('startdate',default='yesterday')
    if startdate=='yesterday':
        startdate = yesterday
    dates = {'lastupdate':lastupdate, 'yesterday':yesterday, 
    'lastweek':lastweek, 'lastmonth':lastmonth,
    'startdate':startdate, 'enddate':enddate}


    showspecials = request.args.get('specials',default='true')
    dates['specials']=showspecials
    queryignorespecials=''
    if showspecials.lower() == 'false':
        showspecials=False
        dates['specials']=False
        queryignorespecials = " and o1.promobadgeimagelabel=='' and o2.promobadgeimagelabel==''"



    conn = opendbconn()
    changes = conn.execute(
        'select o1.productid, o1.productname, o1.obsdate, o1.obsprice, o1.promobadgeimagelabel,\
        o2.obsdate, o2.obsprice, o2.promobadgeimagelabel, o1.scanname, o1.productweighttext, o2.productweighttext\
        from observations o1 inner join observations o2 on o1.productid=o2.productid where \
        o1.obsdate = ? and o2.obsdate=? and o1.obsprice<>o2.obsprice'+queryignorespecials, [startdate,enddate]
    ).fetchall()
    conn.close()    
    increases = []
    decreases = []

    numi = 0
    numd = 0

    for r in changes:
        id = r[0]
        gid = re.match('(\d*)-', r[0])
        id = gid[0]
        if r[6]>r[3]:
            if len(increases)==0 or r[8]!=increases[-1]['scan']:
                increases.append({'header':True, 'scan':r[8]})
            increases.append({'id':id, 'name':r[1], 'sprice':r[3], 'spromo':r[4], 
            'eprice':r[6], 'epromo':r[7], 'spweight':r[9], 'epweight':r[10], 'scan':r[8], 'header':False})
            numi = numi+1
        else:
            if len(decreases)==0 or r[8]!=decreases[-1]['scan']:
                decreases.append({'header':True, 'scan':r[8]})
 
            decreases.append({'id':id, 'name':r[1], 'sprice':r[3], 'spromo':r[4], 
            'eprice':r[6], 'epromo':r[7], 'spweight':r[9], 'epweight':r[10], 'scan':r[8], 'header':False})
            numd = numd+1
    dates['numi'] = numi
    dates['numd'] = numd

    return render_template('pricechanges.html', dates=dates, increases=increases, decreases=decreases)


@app.route('/product/<productid>')
def product_prices(productid):
    conn = opendbconn()
    obsrows = conn.execute('select obsdate, obsprice, promobadgeimagelabel, productweighttext, productname, productid from observations where productid like ? order by obsdate desc', [productid + '%']).fetchall()
    conn.close()
    print(len(obsrows))
    price = []
    for o in obsrows:
        price.append({'date':o[0], 'price': o[1], 'promo':o[2], 'pweight':o[3].split('$')[0]})
        prod = {'name': o[4], 'id':o[5]}

    prod['rows'] = len(price)
    dates = {}
    dates['startdate'] = price[0]['date']
    dates['enddate'] = price[-1]['date']
    dates['lastupdate'] = price[0]['date']

    return render_template('productsummary.html', dates=dates, price=price, prod=prod)


@app.route('/category/<category>')
def catprices(category):
    startrow = 0
    numrows = 0
    
    enddate=request.args.get('enddate',default='today')
    lastupdate = last_update()
    if enddate=='today':
        enddate=lastupdate

    dttoday = datetime.strptime(enddate,'%Y-%m-%d')

    dtlastweek = dttoday - timedelta(days=7)
    lastweek = dtlastweek.strftime('%Y-%m-%d')
    dtlastmonth = dttoday - timedelta(days=30)
    lastmonth = dtlastmonth.strftime('%Y-%m-%d')

    date1 = request.args.get('date1',default=lastupdate)
    date2 = request.args.get('date2',default=lastweek)
    date3 = request.args.get('date3',default=lastmonth)

    conn = opendbconn()
    cur1 = conn.execute('select productid,obsdate, obsprice, productname, promobadgeimagelabel, productweighttext from observations where scanname like ? and obsdate=?',[category, date1])
    obsrows1=cur1.fetchall()
    cur2 = conn.execute('select productid, obsdate, obsprice, productname, promobadgeimagelabel, productweighttext from observations where scanname like ? and obsdate=?',[category, date2])
    obsrows2=cur2.fetchall()
    cur3 = conn.execute('select productid,obsdate, obsprice, productname, promobadgeimagelabel, productweighttext from observations where scanname like ? and obsdate=?',[category, date3])
    obsrows3=cur3.fetchall()
    conn.close()

    outputlist = {}

    for prod in obsrows1:
        prodid = prod[0]
        obsdate = prod[1]
        obsprice = prod[2]
        prodname = prod[3]
        promo = prod[4]
        pweight = prod[5].split('$')[0]
        
        gid = re.match('(\d*)-', prodid)
        niceid = gid[0]

        outputlist[prodid] = {
            'name':prodname,
            'pweight':pweight,
            'price1':obsprice,
            'promo1':promo,
            'id':niceid
        }

    for prod in obsrows2:
        prodid = prod[0]
        obsdate = prod[1]
        obsprice = prod[2]
        prodname = prod[3]
        promo = prod[4]
        pweight = prod[5].split("$")[0]
        
        if prodid not in outputlist:
            gid = re.match('(\d*)-', prodid)
            niceid = gid[0]
            outputlist[prodid] = {
                    'name':prodname,
                    'pweight':pweight,
                    'id':niceid,
                    'price1':' - ',
                    'promo1':' - ',
                }   

        outputlist[prodid]['price2'] = obsprice
        outputlist[prodid]['promo2'] = promo
            
    for prod in obsrows3:
        prodid = prod[0]
        obsdate = prod[1]
        obsprice = prod[2]
        prodname = prod[3]
        promo = prod[4]
        pweight = prod[5].split('$')[0]
        
        if prodid not in outputlist:
            gid = re.match('(\d*)-', prodid)
            niceid = gid[0]
            outputlist[prodid] = {
                    'name':prodname,
                    'pweight':pweight,
                    'id':niceid,
                    'price1':' - ',
                    'promo1':' - ',
                    'price2':' - ',
                    'price2':' - ',
                }

        outputlist[prodid]['price3'] = obsprice
        outputlist[prodid]['promo3'] = promo

        # prodrow['dec1'] = prodrow['price1']<prodrow['price2']
        # prodrow['dec2'] = prodrow['price2']<prodrow['price3']
    
    outputlist = outputlist.values()
    for prod in outputlist:
        if 'price2' not in prod:
            prod['price2'] = ' - '
            prod['promo2'] = ' - '
        if 'price3' not in prod:
            prod['price3'] = ' - '
            prod['promo3'] = ' - '
        
        if prod['price1']==' - ' or prod['price2']==' - ':
            prod['cls1']='same'
        elif prod['price1']>prod['price2']:
            prod['cls1'] = 'inc'
        elif prod['price1']<prod['price2']:
            prod['cls1']='dec'
        else:
            prod['cls1']='same'

        if prod['price2']==' - ' or prod['price3']==' - ':
            prod['cls2']='same'
        elif prod['price2']>prod['price3']:
            prod['cls2'] = 'inc'
        elif prod['price2']<prod['price3']:
            prod['cls2']='dec'
        else:
            prod['cls2']='same'

    cat = {
        'name':category,
        'rows':len(obsrows1)
    }

    dates={
        'lastupdate':lastupdate,
        'date1':date1,
        'date2':date2,
        'date3':date3
    }

    return(render_template('category.html', category=cat, dates=dates, prods=outputlist))

        

@app.route('/category')
def categorylist():
    conn = opendbconn()
    cats = conn.execute('select distinct(scanname) from urls').fetchall()
    conn.close()

    catnames = []
    for cat in cats:
        catnames.append(cat[0])


    return render_template('categorylist.html', cats=catnames)


@app.route('/api/pricechanges')
def new_prices():
        
    enddate=request.args.get('enddate',default='today')
    if enddate=='today':
        enddate=last_update()
    
    dttoday = datetime.strptime(enddate,'%Y-%m-%d')
    dtyesterday = dttoday-timedelta(days=1)
    yesterday = dtyesterday.strftime('%Y-%m-%d')
    dtlastweek = dttoday - timedelta(days=7)
    lastweek = dtlastweek.strftime('%Y-%m-%d')
    dtlastmonth = dttoday - timedelta(days=30)
    lastmonth = dtlastmonth.strftime('%Y-%m-%d')
    
    startdate = request.args.get('startdate',default='yesterday')
    if startdate=='yesterday':
        startdate = yesterday

    print('startdate: ' + startdate + ', enddate: ' + enddate)
    
    conn = opendbconn()
    changes = conn.execute(
        'select o1.productid, o1.productname, o1.obsdate, o1.obsprice, o1.promobadgeimagelabel, o2.obsdate, o2.obsprice, o2.promobadgeimagelabel \
        from observations o1 inner join observations o2 on o1.productid=o2.productid where \
        o1.obsdate = ? and o2.obsdate=? and o1.obsprice<>o2.obsprice', [startdate,enddate]
    ).fetchall()
    increases = []
    decreases = []
    for r in changes:
        if r[3]>r[6]:
            increases.append(r)
        else:
            decreases.append(r)
    conn.close()

    return jsonify({'increases':increases, 'decreases': decreases})
