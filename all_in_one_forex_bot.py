from flask import Flask, request, jsonify
import pandas as pd
import yfinance as yf
import ta

app = Flask(__name__)

def fetch_signals(pair='EURUSD=X', timeframe='1m', limit=100):
    interval_map = {
        '1min': '1m',
        '2min': '2m',
        '5min': '5m',
        '15min': '15m'
    }
    if timeframe not in interval_map:
        return {'error': 'Invalid timeframe'}, 400

    try:
        data = yf.download(tickers=pair, period='1d', interval=interval_map[timeframe], progress=False)
        if data.empty:
            return {'error': 'No data found'}, 404

        df = data.copy()
        df.dropna(inplace=True)

        # Indicators
        df['rsi'] = ta.momentum.RSIIndicator(close=df['Close']).rsi()
        macd = ta.trend.MACD(close=df['Close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['momentum'] = ta.momentum.MomentumIndicator(close=df['Close']).momentum()

        latest = df.iloc[-1]
        signal = 'WAIT'

        # Signal logic
        if latest['rsi'] < 30 and latest['macd'] > latest['macd_signal']:
            signal = 'CALL'
        elif latest['rsi'] > 70 and latest['macd'] < latest['macd_signal']:
            signal = 'PUT'

        return {
            'pair': pair,
            'timeframe': timeframe,
            'signal': signal,
            'rsi': round(latest['rsi'], 2),
            'macd': round(latest['macd'], 5),
            'macd_signal': round(latest['macd_signal'], 5),
            'momentum': round(latest['momentum'], 2)
        }

    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/')
def home():
    return 'Forex Signal Bot is Running!'

@app.route('/signal', methods=['GET'])
def get_signal():
    pair = request.args.get('pair', 'EURUSD=X')  # e.g. EURUSD=X, GBPUSD=X, USDJPY=X
    timeframe = request.args.get('timeframe', '1min')  # e.g. 1min, 2min, 5min, 15min
    result = fetch_signals(pair=pair, timeframe=timeframe)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
