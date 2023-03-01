from flask import Flask, jsonify, request,abort
import sqlite3

app = Flask(__name__)

@app.route('/')
def blank():
    return "Grocery price watch"

def opendbconn():
    conn = sqlite3.connect('CheeseWatch.db')
    return conn

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
    enddate = conn.execute('select obsdate from observations order by obsdate desc limit 1').fetchone()
    print(enddate[0])
    enddate=str(enddate[0])
    products = []

    for row in conn.execute('select distinct(productid), productname,scanname,obsprice from observations where obsdate=? and scanname like?',[enddate,scanname]):
        products.append(row)
    conn.close()
    return jsonify(products)

@app.route('/api/pricehistory',methods=['GET'])
def get_pricehistory():
    try:
        productid = request.args.get('productid','')
    except KeyError as e:
        abort(404)
    if productid==None:
        abort(404)

    try:
        enddate=request.args.get('enddate','')
    except KeyError as e:
        enddate = str(conn.execute('select obsdate from observations order by obsdate desc limit 1').fetchone()[0])
        print('No enddate given')
    print('enddate: ' + enddate)
    startdate = request.args.get('startdate',default='2022-12-01')

    print('start date: '+ startdate)
    conn = opendbconn()
    pricehistory = conn.execute('select obsdate, obsprice from observations \
        where productid like ? and obsdate>=? and obsdate<=?',[productid+'%', startdate, enddate],).fetchall()
    if len(pricehistory)==0:
        print('No history')
        return jsonify({'Error':'No history found'})
        
    prices = []
    for row in pricehistory:
        prices.append({'prodname':row[1],'obsdate':row[2], 'obsprice':row[3]} )
    conn.close()
    return jsonify(prices)
    


@app.route('/api/newprices')
def new_prices():
    
    conn = opendbconn()
    
    enddate = conn.execute('select obsdate from observations order by obsdate desc limit 1').fetchone()

