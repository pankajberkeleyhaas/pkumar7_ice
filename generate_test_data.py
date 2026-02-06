import csv
import random

instruments = [
    "Equity", "ETF", "FX", "Options", "Futures", "Swap", "Bonds", 
    "Commodities", "Cryptocurrency", "REIT", "Mutual Fund", "CDS", 
    "Warrant", "Structured Product"
]

comments = {
    "Equity": [
        "Apple looks overvalued at these levels, waiting for a dip.",
        "Tesla's margins are getting squeezed, I'm bearish.",
        "Nvidia is a monster, AI play is just starting.",
        "I'm long on MSFT, dividends are consistent and growth is there.",
        "Penny stocks are a gamble, I lost $5k on some biotech firm."
    ],
    "ETF": [
        "S&P 500 ETFs like VOO are the safest bet for long term.",
        "I'm switching from QQQ to SCHD for more dividend exposure.",
        "The expense ratio on this thematic ETF is way too high.",
        "Leveraged ETFs are dangerous if you don't know what you're doing.",
        "VTI and chill is my retirement strategy."
    ],
    "FX": [
        "EUR/USD is testing the 1.08 support level again.",
        "Jena weakness is hurting my carry trade.",
        "The Fed's hawkish stance is pumping the DXY.",
        "Forex trading is a zero-sum game, stick to indices.",
        "GBP is looking strong after the latest economic data."
    ],
    "Options": [
        "Sold some covered calls on my AMC position to lower cost basis.",
        "0DTE options are basically a casino, stay away.",
        "Theta decay is killing my long calls on NVDA.",
        "Buying puts on the market, I think a correction is coming.",
        "Iron condors on SPY have been working well this month."
    ],
    "Futures": [
        "Oil futures are spiking due to geopolitical tensions.",
        "Corn futures look cheap, might be a good entry point.",
        "Trading ES futures is much better than SPY for leverage.",
        "The contango in VIX futures is insane right now.",
        "Margin calls on Nasdaq futures destroyed my account."
    ],
    "Swap": [
        "Interest rate swaps are getting complicated with the new LIBOR transition.",
        "The company entered into a currency swap to hedge debt exposure.",
        "Total return swaps are being used by hedge funds for hidden leverage.",
        "Credit default swaps spreads are widening for regional banks.",
        "Equity swaps are a great way to get exposure without owning the stock."
    ],
    "Bonds": [
        "10-year Treasury yields are hitting levels we haven't seen in a decade.",
        "Junk bonds are looking risky with the upcoming recession fears.",
        "Municipal bonds are great for tax-free income if you're in a high bracket.",
        "Bond prices fall when interest rates rise, simple math.",
        "Corporate bonds are offering better yields than most savings accounts."
    ],
    "Commodities": [
        "Gold is a safe haven when the dollar is weakening.",
        "Lithium prices are crashing, bad news for EV battery stocks.",
        "Natural gas volatility is off the charts this winter.",
        "Investing in physical silver is the only way to play the squeeze.",
        "Coffee prices are up due to poor harvests in Brazil."
    ],
    "Cryptocurrency": [
        "Bitcoin is the new digital gold, HODL till 100k.",
        "Ethereum's gas fees are still too high for small transactions.",
        "Solana is fast but the network outages are a major red flag.",
        "Dogecoin is for the memes, don't put life savings into it.",
        "CBDCs are coming and they will kill privacy in crypto."
    ],
    "REIT": [
        "Commercial real estate REITs are a ticking time bomb.",
        "Data center REITs like Equinix are the backbone of the internet.",
        "Residential REITs are benefiting from the housing shortage.",
        "The 7% dividend yield on this REIT looks too good to be true.",
        "O (Realty Income) is the king of monthly dividends."
    ],
    "Mutual Fund": [
        "Active mutual funds rarely beat their benchmarks over time.",
        "My 401k is mostly in Vanguard mutual funds.",
        "Exit loads on mutual funds are a pain if you need liquidity.",
        "The fund manager's track record is the most important factor.",
        "Stop paying 1% management fees for a closet indexer."
    ],
    "CDS": [
        "CDS spreads on Credit Suisse were a huge warning sign.",
        "Betting against the housing market with CDS was 'The Big Short'.",
        "Sovereign CDS for emerging markets is getting expensive.",
        "The counterparty risk in the CDS market is underestimated.",
        "CDS is basically insurance for bondholders."
    ],
    "Warrant": [
        "Stock warrants are a great way to get cheap leverage on IPOs.",
        "The exercise price on these warrants is way out of the money.",
        "Don't forget the expiration date on your warrants or they go to zero.",
        "Warrant dilution is a real concern for long-term shareholders.",
        "Company issued warrants to sweeten the bond offering."
    ],
    "Structured Product": [
        "Principal protected notes are for people who hate risk.",
        "Reverse convertibles offer high yields but high downside risk.",
        "Market-linked CDs are just structured products in disguise.",
        "The complexity of these notes makes it hard to price correctly.",
        "Autocallables are great in a sideways market."
    ]
}

def generate_data(num_points=100):
    output_file = "financial_instrument_comments.csv"
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Financial Instrument", "Body"])
        
        for _ in range(num_points):
            instrument = random.choice(instruments)
            # Pick a comment from the list for that instrument, 
            # or a generic one if the instrument list is small
            body = random.choice(comments.get(instrument, ["Interesting market movement today.", "Researching for my portfolio."]))
            writer.writerow([instrument, body])
    
    print(f"Generated {num_points} data points in {output_file}")

if __name__ == "__main__":
    generate_data(100)
