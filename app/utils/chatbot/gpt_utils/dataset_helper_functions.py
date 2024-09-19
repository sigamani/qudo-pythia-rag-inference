import re
import pandas as pd
import openai


def strip_html(x):
    """Function to strip html tags from the string"""
    x = str(x)
    try:
        return re.sub("<[^<]+?>", "", x)
    except:
        raise ValueError(f"Inspect regex for {x}")


def remove_contraction_apostraphes(input):
    text = re.sub("([A-Za-z]+)['`]([A-Za-z]+)", r"\1" r"\2", input)
    return text


extra_title_mapping = {
    "varname": [
        "sbeh_ww_financialattitudes_rbg_ord_confidence",
        "sbeh_ww_financialattitudes_rbg_ord_spendingspeed",
        "sbeh_ww_financialattitudes_rbg_ord_consideration_gg",
        "sbeh_ww_financialattitudes_rbg_ord_moneyimportance_fb",
        "sbeh_ww_financialattitudes_rbg_ord_loyalty",
        "sbeh_ww_financialattitudes_rbg_ord_borrowing",
        "sbeh_ww_financialattitudes_rbg_ord_earlyadoption_fb",
        "sbeh_ww_financialattitudes_rbg_ord_risk_gg",
        "sbeh_ww_financialbehaviour01_rbg_ord_paidbillsontime",
        "sbeh_ww_financialbehaviour01_rbg_ord_mademinpayment",
        "sbeh_ww_financialbehaviour01_rbg_ord_trackedmonthlyexpenses",
        "sbeh_ww_financialbehaviour01_rbg_ord_shopcompared",
        "sbeh_ww_financialbehaviour01_rbg_ord_stayedwithinbudget",
        "sbeh_ww_financialbehaviour01_rbg_ord_attentiontrap",
        "sbeh_ww_financialbehaviour01_rbg_ord_paidofffullccbalance",
        "sbeh_ww_financialbehaviour01_rbg_ord_maxedoutcreditcards",
        "sbeh_us_financialbehaviour02_rbg_ord_retirement_gg",
        "sbeh_us_financialbehaviour02_rbg_ord_switchbank_gg",
        "sbeh_us_financialbehaviour02_rbg_ord_invested_gg",
        "sbeh_us_financialbehaviour02_rbg_ord_emergencyfund_gg",
        "sbeh_us_financialbehaviour02_rbg_ord_savedforltplan",
        "sbeh_us_financialbehaviour02_rbg_ord_savedregularly",
        "sbeh_us_financialbehaviour02_rbg_ord_checkedcreditscore_gg",
        "sbeh_us_financialbehaviour02_rbg_ord_checkedbalance_gg",
    ],
    "extra": [
        "I am confident managing my money",
        "I spend money as soon as I get it",
        "Before I buy something, I carefully consider if I can afford it",
        "My life revolves around money",
        "I like to stick with the financial brands I know",
        "I am comfortable borrowing – it feels quite normal to me",
        "I am amongst the first to use innovative financial products / apps",
        "I am comfortable taking financial risk / investing",
        "Paid all bills on time",
        "Made only minimum payments on a loan",
        "Tracked monthly expenses",
        "Shopped on comparison websites for a product or service",
        "Stayed within budget or spending plan",
        "Please skip answering this row",
        "Paid off credit balance in full each month",
        "Maxed out the limit on one or more credit cards",
        "Contributed to a retirement plan",
        "Considered switching my bank",
        "Invested money",
        "Began or maintained an emergency savings fund",
        "Saved for a long-term goal",
        "Saved money from every paycheque",
        "Checked my credit score",
        "Checked my checking account balance",
    ],
}

extra_title_mapping_df = pd.DataFrame(extra_title_mapping)


def extra_title_fixer(x):
    """Function to make question title less ambiguous"""
    if x["varname"] in list(extra_title_mapping_df["varname"]):
        try:
            return (
                x["title"]
                + ": "
                + extra_title_mapping_df[extra_title_mapping_df["varname"] == x["varname"]]["extra"].values[0]
            )
        except:
            raise ValueError("Inspect extra_title_fixer.")
    else:
        return x["title"]


ambiguous_questions = [
    "Which of the following is true in your case? Please select all that apply or skip if none are applicable.",
    "Which of the following is the most like you?",
    "Which of the following have you used in the past 12 months? Please select all that apply or skip if not applicable",
    "Which of the following represents your situation the best?",
    "Please select all statements that are true in your case. Skip if none are applicable.",
    "Please indicate how often you want to skip answering this row",
    "Which of the following correctly describes your situation?",
    "Please select all the statements to which you either agree or strongly agree.",
]


def ambiguous_title_fixer(x):
    if x["title"] == "Please select all the statements to which you either agree or strongly agree.":
        print("stop")
    if x["title"] in ambiguous_questions:
        return x["title"] + ": " + x["option_text"]
    else:
        return x["title"]


def split_list(a, n):
    k, m = divmod(len(a), n)
    return list((a[i * k + min(i, m) : (i + 1) * k + min(i + 1, m)] for i in range(n)))


def get_embedding(text, model="text-embedding-ada-002"):
    """Function to embed text via GPT embedding model."""
    text = text.replace("\n", " ")
    return openai.Embedding.create(input=[text], model=model)["data"][0]["embedding"]


def extract_segment_df(value):
    """Function to extract the chi2 question (define) answer couplets for a segment
    and filter out non-informative answers."""
    segment_df = value["segment_df"][["segment", "question", "define"]].drop_duplicates()
    segment_df = segment_df[segment_df["define"] != "."]
    segment_df = segment_df.dropna(subset=["define"])
    return segment_df
