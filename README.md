### Stock Trading Simulator

A website lets users simulate trading in the stock market using Flask and SQLite3.

Users have to register for their own accounts. After registering and logging into user's account, user can search for stock's quote, "buy" and "sell" stocks at stock market live price, as well ask check current stock holdings and trading history. Each user starts with $10,000 "cash" after registration.

### IEX

The stock market live price is queried from [IEX](https://exchange.iex.io/products/market-data-connectivity/).  
IEX lets you download stock quotes via their API (application programming interface) using URLs like `https://cloud-sse.iexapis.com/stable/stock/nflx/quote?token=API_KEY`. In the sample URL, Netflix’s symbol (NFLX) is embedded in this URL; that’s how IEX knows whose data to return. That link won’t actually return any data because IEX requires you to use an API key.

### Configuring

Before launching this website, you need to register for an API key in order to be able to query IEX’s data. To do so, follow these steps:

1. Visit [iexcloud.io/cloud-login#/register/](https://iexcloud.io/cloud-login#/register/).
2. Select the “Individual” account type, then enter your name, email address, and a password, and click “Create account”.
3. Once registered, scroll down to “Get started for free” and click “Select Start plan” to choose the free plan.
4. Once you’ve confirmed your account via a confirmation email, visit [https://iexcloud.io/console/tokens](https://iexcloud.io/console/tokens).
5. Copy the key that appears under the Token column (it should begin with pk\_).
6. In your terminal window, execute:
    ```bash
    export API_KEY=value
    ```
    where value is that (pasted) value, without any space immediately before or after the =. You also may wish to paste that value in a text document somewhere, in case you need it again later.

### Installation

To open this website, you need to have below packages installed:

1. [Flask](https://flask.palletsprojects.com/en/2.1.x/installation/)
    ```
    pip install Flask
    ```
2. [Flask-Session](https://flask-session.readthedocs.io/en/latest/)
    ```
    pip install Flask-Session
    ```
3. [urllib3](https://pypi.org/project/urllib3/)
    ```
    pip install urllib3
    ```
4. [requests](https://pypi.org/project/requests/)
    ```
    pip install requests
    ```
5. [Werkzeug](https://werkzeug.palletsprojects.com/en/2.1.x/installation/)
    ```
    pip install Werkzeug
    ```

### Run the application

To open this website, run below:

```bash
flask run
```
