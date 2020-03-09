import pandas as pd
import numpy as np
from itertools import combinations, product


def process_data():
    # Create card vectors
    data = pd.read_csv('card_data.csv')
    categories = list(data.columns)[2:]
    card_names = list(data.Card_Name)

    card_vectors = data[categories]
    us_bank_cats = card_vectors.loc[0, card_vectors.columns !=
                                    'Foreign_Transactions'].to_numpy().nonzero()[0]
    boa_cats = card_vectors.loc[4, card_vectors.columns !=
                                'Foreign_Transactions'].to_numpy().nonzero()[0]
    us_bank_combinations = combinations(us_bank_cats, 2)
    boa_combinations = combinations(boa_cats, 1)

    us_bank_vec = []
    for c in us_bank_combinations:
        temp_row = np.zeros(len(categories))
        temp_row[list(c)] = card_vectors.iloc[0][list(c)]
        us_bank_vec.append(temp_row)
        card_names.append(card_names[0])
    us_bank_df = pd.DataFrame(us_bank_vec, columns=categories)

    boa_vec = []
    for c in boa_combinations:
        temp_row = np.zeros(len(categories))
        temp_row[list(c)[0]] = card_vectors.iloc[4][list(c)[0]]
        boa_vec.append(temp_row)
        card_names.append(card_names[4])
    boa_df = pd.DataFrame(boa_vec, columns=categories)

    card_vectors = card_vectors.drop(
        index=card_vectors.index[[0, 4]]).reset_index(drop=True)
    card_vectors = card_vectors.append(us_bank_df, ignore_index=True)
    card_vectors = card_vectors.append(boa_df, ignore_index=True)
    del card_names[4]
    del card_names[0]

    comb_dict = {}
    for i in range(0, 15):
        comb_dict[card_names[i]] = [i]
    comb_dict[card_names[15]] = list(range(15, 25))
    comb_dict[card_names[26]] = list(range(25, 29))
    return comb_dict, card_vectors, card_names


def calc_cb(comb_dict, num_cards, card_vectors, spend, attr):
    max_cb = 0
    member = {}
    # Iterate through all combinations based on rules set by dictionary
    for comb in combinations(sorted(comb_dict), num_cards):
        for uniquecomb in product(*[comb_dict[i] for i in comb]):
            # print(card_vectors.iloc[list(uniquecomb),:].max(axis=0))
            temp_cb = 0
            if 7 in uniquecomb and num_cards > 1:
                # calculate discover cash back advantage
                # calculate earnings in cats
                temp_cb = sum(np.multiply(
                    card_vectors.iloc[7, :].to_numpy(), spend))
                # get non-discover cards in uniquecomb
                other_cards = [card for card in uniquecomb if card != 7]
                cb_indices = list(card_vectors.iloc[7, :].to_numpy().nonzero())[
                    0]  # indices of discover categories
                other_cb = sum(np.multiply(
                    card_vectors.iloc[other_cards, cb_indices].to_numpy()[0], spend[cb_indices]))
                # discover cash back in cats - other cards in those same cats over 4
                temp_cb = (temp_cb - other_cb) / 4
                all_other_cb = sum(np.multiply(card_vectors.iloc[other_cards, :].to_numpy()[
                                   0], spend))  # leave out discover
                temp_cb += all_other_cb  # add net cb to all other cards
            elif 7 in uniquecomb:
                temp_cb = sum(np.multiply(
                    card_vectors.iloc[7, :].to_numpy(), spend)) / 4
            else:
                best_cb = card_vectors.iloc[list(uniquecomb), :].max(axis=0)
                temp_cb = sum(np.multiply(best_cb, spend))
            # Annual fee deductions
            if 1 in uniquecomb:
                temp_cb -= 95 / 12
            if 6 in uniquecomb:
                temp_cb -= 99 / 12
            if 15 in uniquecomb:
                temp_cb -= 95 / 12
            # Membership costs
            if 11 in uniquecomb and not attr['sams_member']:
                temp_cb -= 45 / 12
            if 3 in uniquecomb and not attr['amazon_member']:
                temp_cb -= 119 / 12
            if 0 in uniquecomb and not attr['costco_member']:
                temp_cb -= 60 / 12
            if temp_cb > max_cb:
                max_cb = temp_cb
                best_combo = uniquecomb
                if 11 in uniquecomb and not attr['sams_member']:
                    # We will recommend getting a sam's membership
                    member['SC'] = True
                if 3 in uniquecomb and not attr['amazon_member']:
                    # Recommend getting amazon membership
                    member['AMZN'] = True
                if 0 in uniquecomb and not attr['costco_member']:
                    # Recommend getting costco membership
                    member['COSTCO'] = True

    select_cat = {}
    # Which categories of choose cards selected?
    for card in best_combo:
        if card_names[card] == card_names[15]:
            s = card_vectors.iloc[card]
            select_cat['us_bank'] = list(s.axes[0][s > 0])
        if card_names[card] == card_names[25]:
            s = card_vectors.iloc[card]
            select_cat['boa'] = list(s.axes[0][s > 0])
    return max_cb, best_combo, member, select_cat


def calc_stats(spend, max_cb):
    avg_cb = max_cb / sum(spend)
    annual_cb = max_cb * 12
    return avg_cb, annual_cb


if __name__ == "__main__":
    # Get User Input
    print("Please enter avg. monthly spend for the following categories:\n")
    spend, attr = [], {}  # spend and attributes
    total_spend = int(input("Total monthly credit card bills: $"))
    spend.append(int(input("Groceries: $")))
    spend.append(int(input("Gas: $")))
    spend.append(int(input("Eating out: $")))
    spend.append(int(input(
        "Entertainment (movies, plays, concert tickets, sporting events, etc.) : $")))
    spend.append(int(input("Travel: $")))
    spend.append(int(input("Utilities: $")))
    spend.append(
        int(input("Cell phone carrier (including purchases made at physical store)): $")))
    spend.append(int(input("Gym/Fitness Memberships: $")))
    spend.append(int(input("Online Shopping (not including Amazon): $")))
    spend.append(int(input("Amazon.com: $")))
    spend.append(int(input("Home Improvement Stores: $")))
    spend.append(int(input("Internet, Cable, and Streaming Services: $")))
    spend.append(int(input("Sporting good stores: $")))
    spend.append(int(input("Apple store: $")))
    spend.append(int(input("Foreign transactions: $")))
    spend.append(int(input("Rideshare (Uber, Lyft): $")))
    spend.append(max(total_spend - sum(spend), 0))  # Other expenses
    spend = np.array(spend)

    attr['amazon_member'] = True if input(
        "Amazon member? Y/N: ").lower() == "y" else False
    attr['costco_member'] = True if input(
        "Costco member? Y/N: ").lower() == "y" else False
    attr['sams_member'] = True if input(
        "Sam's Club member? Y/N: ").lower() == "y" else False
    attr['boa'] = True if input(
        "Existing BoA accounts? Y/N: ").lower() == "y" else False
    if attr['boa']:
        boa_amt = int(
            input("How much capital do you have in existing BoA accounts?: "))
        if boa_amt >= 100000:
            multiplier = 1.75
        elif boa_amt >= 50000:
            multiplier = 1.5
        elif boa_amt >= 20000:
            multiplier = 1.25

    # Process data and make calculations

    data = pd.read_csv('card_data.csv')

    comb_dict, card_vectors, card_names = process_data()
    num_cards = int(input("Preferred number of cards?\n"))
    max_cb, best_combo, member, select_cat = calc_cb(
        comb_dict, num_cards, card_vectors, spend, attr)
    avg_cb, annual_cb = calc_stats(spend, max_cb)

    cards = [card_names[i] for i in best_combo]
    for card in cards:
        print(card)

    print(f"\nAvg cash back: {avg_cb:.4f}",
          f"\nAnnual cash back: ${annual_cb:.2f}")
    print(f"Total annual spend: ${12*sum(spend):.2f}")
