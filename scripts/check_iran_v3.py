import requests
# Get latest price for NO and YES
tid_no = "51938013536033607392847872760095315790110510345353215258271180769721415981927"
tid_yes = "5708561660601459805512817131601230493971589760294984590237789749933853841330"

def get_price(tid):
    try:
        url = f"https://clob.polymarket.com/price?token_id={tid}&side=buy"
        return requests.get(url).json().get('price')
    except:
        return "Error"

print(f"NO Price: {get_price(tid_no)}")
print(f"YES Price: {get_price(tid_yes)}")
