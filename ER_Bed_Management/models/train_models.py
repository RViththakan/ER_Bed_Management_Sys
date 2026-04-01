import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import LabelEncoder

def train():
    df = pd.read_csv('../data/Ontario_ER_Wait_Time_Master_Final.csv')

    # Encoding
    le_condition = LabelEncoder()
    df['Condition_Enc'] = le_condition.fit_transform(df['Condition Category'])
    
    le_ctas = LabelEncoder()
    df['CTAS_Enc'] = le_ctas.fit_transform(df['CTAS Level'])
    
    df['is_discharged'] = (df['Patient Outcome'] == 'Discharged').astype(int)

    # Features and Targets
    features = ['Age', 'Condition_Enc', 'CTAS_Enc', 'Nurse-to-Patient Ratio', 'Specialist Availability']
    X = df[features]
    
    # Model 1: Discharge Prediction
    cls_model = RandomForestClassifier(n_estimators=100).fit(X, df['is_discharged'])
    
    # Model 2: Time Remaining Prediction
    reg_model = RandomForestRegressor(n_estimators=100).fit(X, df['Total Wait Time (min)'])

    # Save everything
    joblib.dump(cls_model, 'classifier_model.joblib')
    joblib.dump(reg_model, 'regressor_model.joblib')
    joblib.dump(le_condition, 'le_condition.joblib')
    joblib.dump(le_ctas, 'le_ctas.joblib')
    print("Models trained and saved successfully!")

if __name__ == "__main__":
    train()