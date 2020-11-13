import otherfxns as o

isPaper = bool(o.c['isPaper']) #set up as paper trading (testing), or actual trading
keyFile = open(o.c['keyFile'],"r")
apiKeys = o.json.loads(keyFile.read())
keyFile.close()
  
if(isPaper):
  APIKEY = apiKeys["ALPACAPAPERKEY"]
  SECRETKEY = apiKeys["ALPACAPAPERSECRETKEY"]
  ENDPOINTURL = apiKeys["ALPACAPAPERURL"]
else:
  APIKEY = apiKeys["ALPACAKEY"]
  SECRETKEY = apiKeys["ALPACASECRETKEY"]
  ENDPOINTURL = apiKeys["ALPACAURL"]
  
HEADERS = {"APCA-API-KEY-ID":APIKEY,"APCA-API-SECRET-KEY":SECRETKEY} #headers for data

#alpaca = alpacaapi.REST(APIKEY,SECRETKEY,ENDPOINTURL,api_version="v2")
ACCTURL = "{}/v2/account".format(ENDPOINTURL) #account url
ORDERSURL = "{}/v2/orders".format(ENDPOINTURL) #orders url
POSURL = "{}/v2/positions".format(ENDPOINTURL) #positions url
CLKURL = "{}/v2/clock".format(ENDPOINTURL) #clock url
CALURL = "{}/v2/calendar".format(ENDPOINTURL) #calendar url
ASSETURL = "{}/v2/assets".format(ENDPOINTURL) #asset url

# return string of account info
def getAcct():
  while True:
    try:
      html = o.requests.get(ACCTURL, headers=HEADERS, timeout=5).content
      break
    except Exception:
      print("No connection, or other error encountered in getAcct. Trying again...")
      o.time.sleep(3)
      continue

  return o.json.loads(html)

# return currently held positions/stocks/whatever
def getPos():
  while True:
    try:
      html = o.requests.get(POSURL, headers=HEADERS, timeout=5).content
      break
    except Exception:
      print("No connection, or other error encountered in getPos. Trying again...")
      o.time.sleep(3)
      continue
  return o.json.loads(html)

# return currently held positions/stocks/whatever
def getOrders():
  while True:
    try:
      html = o.requests.get(ORDERSURL, headers=HEADERS, timeout=5).content
      break
    except Exception:
      print("No connection, or other error encountered in getOrders. Trying again...")
      o.time.sleep(3)
      continue

  return o.json.loads(html)

#can prompt the user to consent to removing all orders and positions (starting over from scratch)
#returns 1 if trades were made, 0 if no trades made
def sellAll(isManual=1):
  pos = getPos()
  orders = getOrders()
  if(len(pos)+len(orders)>0):
    if(isManual):
      doit = input('Sell and cancel all positions and orders (y/n)? ')
    else:
      doit="y"

    if(doit=="y"): #user consents
      print("Removing Orders...")
      while True:
        try:
          r = o.requests.delete(ORDERSURL, headers=HEADERS, timeout=5)
          break
        except Exception:
          print("No connection, or other error encountered in sellAll. Trying again...")
          o.time.sleep(3)
          continue
      r = o.json.loads(r.content.decode("utf-8"))
      for e in r:
        print(e["body"]["symbol"])
      print("Orders Cancelled.")
      #sell positions
      for p in pos:
        print("Selling "+p["qty"]+" share(s) of "+p["symbol"])
        createOrder("sell",p["qty"],p["symbol"],"market","day")
      print("Done Selling.")
      return 1
    else:
      print("Selling cancelled.")
      return 0
  else:
    print("No shares held")
    return 0


#look to buy/sell a position
def createOrder(side, qty, sym, orderType="market", time_in_force="day", limPrice=0):
  if(o.isTradable(sym)):
    order = {
      "symbol":sym,
      "qty":qty,
      "type":orderType,
      "side":side,
      "time_in_force":time_in_force
    }
    if(orderType=="limit"): #TODO: this returns an error if used. Fix
      order['take_profit'] = {'limit_price':str(limPrice)}
    while True:
      try:
        r = o.requests.post(ORDERSURL, json=order, headers=HEADERS, timeout=5)
        break
      except Exception:
        print("No connection, or other error encountered in createOrder. Trying again...")
        o.time.sleep(3)
        continue
  
    r = o.json.loads(r.content.decode("utf-8"))
    # print(r)
    try:
      #TODO: add trade info here?
      return "Order to "+r["side"]+" "+r["qty"]+" share(s) of "+r["symbol"]+" at "+r["updated_at"]+" - "+r["status"]
    except Exception:
      return "Error: "+o.json.dumps(r)
  else:
    return sym+" is not tradable"

#check if the market is open
def marketIsOpen():
  while True:
    try:
      r = o.json.loads(o.requests.get(CLKURL, headers=HEADERS, timeout=5).content)
      break
    except Exception:
      print("No connection, or other error encountered in marketIsOpen. Trying again...")
      o.time.sleep(3)
      continue
  return r["is_open"]

#current market time in seconds since midnight
def marketTime():
  while True:
    try:
      ts = o.json.loads(o.requests.get(CLKURL, headers=HEADERS, timeout=5).content)["timestamp"]
      break
    except Exception:
      print("No connection, or other error encountered in marketTime. Trying again...")
      o.time.sleep(3)
      continue

  ts = o.re.split('[-:T.]',ts[:-2])[:-3]
  ts = [int(ts[0]), int(ts[1]), int(ts[2]), int(ts[3])*3600+int(ts[4])*60+int(ts[5])]
  return ts

#time until next market close - in seconds
def timeTillClose():
  while True:
    try:
      cl = o.json.loads(o.requests.get(CLKURL, headers=HEADERS, timeout=5).content)["next_close"]
      break
    except Exception:
      print("No connection, or other error encountered in timeTillClose. Trying again...")
      o.time.sleep(3)
      continue

  cl = o.re.split('[-:T.]',cl[:-2])
  cl = o.dt.datetime(int(cl[0]),int(cl[1]),int(cl[2]),int(cl[3]),int(cl[4]))
  now = marketTime()
  now = o.dt.datetime(int(now[0]),int(now[1]),int(now[2]),int(now[3]/3600),int(now[3]%3600/60),int(now[3]%60))
  return (cl - now).total_seconds()

#time until next market open - in seconds
def timeTillOpen():
  while True:
    try:
      op = o.json.loads(o.requests.get(CLKURL, headers=HEADERS, timeout=5).content)["next_open"]
      break
    except Exception:
      print("No connection, or other error encountered in timeTillOpen. Trying again...")
      o.time.sleep(3)
      continue

  op = o.re.split('[-:T.]',op[:-2])
  op = o.dt.datetime(int(op[0]),int(op[1]),int(op[2]),int(op[3]),int(op[4]))
  now = marketTime()
  now = o.dt.datetime(int(now[0]),int(now[1]),int(now[2]),int(now[3]/3600),int(now[3]%3600/60),int(now[3]%60))
  return (op - now).total_seconds()

#return the open and close times of a given day (EST)
def openCloseTimes(checkDate): #checkdate of format yyyy-mm-dd
  calParams = {}
  calParams["start"] = checkDate
  calParams["end"] = checkDate
  while True:
    try:
      d = o.json.loads(o.requests.get(CALURL, headers=HEADERS, params=calParams, timeout=5).content)[0]
      break
    except Exception:
      print("No connection, or other error encountered in openCloseTimes. Trying again...")
      o.time.sleep(3)
      continue
  
  #subtract 1 from hours to convert from EST (NYSE time), to CST (my time)
  d["open"] = str(int(d["open"].split(":")[0])-1)+":"+d["open"].split(":")[1]
  d["close"] = str(int(d["close"].split(":")[0])-1)+":"+d["close"].split(":")[1]
  return [o.dt.datetime.strptime(d["date"]+d["open"],"%Y-%m-%d%H:%M"), o.dt.datetime.strptime(d["date"]+d["close"],"%Y-%m-%d%H:%M")]

# return the current price of the indicated stock
def getPrice(symb):
  symb = symb.upper() #make sure it's uppercase, otherwise it may error out
  #using the alpaca link is faster, but the nasdaq link updates the prices more frequently
  url = 'https://api.nasdaq.com/api/quote/{}/info?assetclass=stocks'.format(symb) #use this URL to avoid alpaca
  #url = 'https://data.alpaca.markets/v1/last/stocks/{}'.format(symb)
  while True:
    try:
      #response = o.requests.get(url,headers=HEADERS, timeout=5).text #send request and store response
      response = o.requests.get(url,headers={"User-Agent": "-"}, timeout=5).text #nasdaq url requires a non-empty user-agent string
      break
    except Exception:
      print("No connection, or other error encountered in getPrice. Trying again...")
      o.time.sleep(3)
      continue

  try:
    latestPrice = float(o.json.loads(response)["data"]["primaryData"]["lastSalePrice"][1:]) #use this line for the alt. URL
    #latestPrice = float(o.json.loads(response)['last']['price'])
    return latestPrice
  except Exception:
    print("Invalid Stock - "+symb)
    return 0

#make sure that we can trade it on alpaca too
def isAlpacaTradable(symb):
  while True:
    try:
      tradable = o.requests.get(ASSETURL+"/"+symb, headers=HEADERS, timeout=5).content
      break
    except Exception:
      print("No connection, or other error encountered in isAlpacaTradable. Trying again...")
      o.time.sleep(3)
      continue
  try:
    return o.json.loads(tradable)['tradable']
  except Exception:
    return False


def checkValidKeys():
  while True:
    try:
      test = getAcct()
      break
    except Exception:
      print("No connection, or other error encountered in checkValidKeys. Trying again...")
      o.time.sleep(3)
      continue
  try:
    test = test["status"]
    if(test=="ACTIVE"):
      print("Valid keys - active account",end="")
      if(isPaper):
        print(" - paper trading")
      else:
        print(" - live trading")
    else:
      print("Valid keys - inactive account")
  except Exception:
    try:
      test = test['message']
      print("Invalid keys")
    except Exception:
      print("Unknown issue encountered.")
    o.sys.exit()

#TODO: add this function - see https://alpaca.markets/docs/api-documentation/api-v2/account-activities/
#get the trades made on a specified date  
def getTrades(date):
  while True:
    try:
      d = o.json.loads(o.requests.get(ACCTURL+"/activities/FILL", headers=HEADERS, params={"date":date}, timeout=5).content)
      break
    except Exception:
      print("No connection, or other error encountered in getTrades. Trying again...")
      o.time.sleep(3)
      continue
  return d

#get all trades for a given stock from a given start date to today
def getStockTrades(symb,startDate=str(o.dt.date.today())):
  r = []
  while True:
    try:
      d = o.json.loads(o.requests.get(ACCTURL+"/activities/FILL", headers=HEADERS, params={"after":startDate}, timeout=5).content)
      while(len(d)==100 or len(r)==100):
        r = o.json.loads(o.requests.get(ACCTURL+"/activities/FILL", headers=HEADERS, params={"after":startDate,"page_token":d[-1]['id']}, timeout=5).content)
        d += r
      break
    except Exception:
      print("No connection, or other error encountered in getStockTrades. Trying again...")
      o.time.sleep(3)
      continue
  
  out = [e for e in d if e['symbol']==symb.upper()]
  
  return out


#get the avg price a stock was bought at since the last sell
def getBuyPrice(symb):
  '''
  average the stock's buy prices from the minimum of the jump date or when the last sell was
  '''
  #get the latest jump date
  jumpDate = o.goodBuy(symb,200)
  
  try: #make sure that the jump date is valid, if not, try getting the average price paid overall, otherwise just return 0
    jumpDate = str(o.dt.datetime.strptime(jumpDate, "%m/%d/%Y")) #convert to standard yyyy-mm-dd format
  except Exception:
    print("error finding recent jump date")
    try:
      p = getPos()
      avg = float([e for e in p if e['symbol']==symb.upper()][0]['avg_entry_price'])
      print("returning overall average price")
      return avg
    except Exception:
      print("error finding overall average")
      return 0

  t = getStockTrades(symb, jumpDate) #get all trades for the stock
  
  #find the latest sell date
  i=0
  while i<len(t) and t[i]['side']=="buy":
    i += 1
  
  #return the avg, or if no data found (or latest trade was a sell), return 0
  if(i>0):
    totalSpent = sum([float(e['price'])*float(e['qty']) for e in t[:i]])
    totalQty = sum([float(e['qty']) for e in t[:i]])
    return totalSpent/totalQty
  else:
    return 0


