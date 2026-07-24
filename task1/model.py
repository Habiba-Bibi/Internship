import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.impute import SimpleImputer
import joblib

def main():
    print("Loading data...")
    df = pd.read_csv('intern_dataset_realistic (1).csv')
    
    # Define features and target
    features = ['Completion_Time', 'Feedback_Rating', 'Attendance']
    target = 'Performance_Score'
    
    X = df[features]
    y = df[target]
    
    print("Handling missing values...")
    # Impute missing values with mean
    imputer = SimpleImputer(strategy='mean')
    X_imputed = imputer.fit_transform(X)
    
    # Handle possible missing values in target
    y_imputer = SimpleImputer(strategy='mean')
    y_imputed = y_imputer.fit_transform(y.values.reshape(-1, 1)).ravel()
    
    print("Splitting data...")
    X_train, X_test, y_train, y_test = train_test_split(X_imputed, y_imputed, test_size=0.2, random_state=42)
    
    print("Training Random Forest...")
    rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)
    rf_preds = rf_model.predict(X_test)
    
    print("Training XGBoost...")
    xgb_model = XGBRegressor(n_estimators=100, random_state=42)
    xgb_model.fit(X_train, y_train)
    xgb_preds = xgb_model.predict(X_test)
    
    print("\n--- Model Evaluation ---")
    print(f"Random Forest MSE: {mean_squared_error(y_test, rf_preds):.4f}, R2: {r2_score(y_test, rf_preds):.4f}")
    print(f"XGBoost MSE:       {mean_squared_error(y_test, xgb_preds):.4f}, R2: {r2_score(y_test, xgb_preds):.4f}")
    
    # Determine best model for full dataset predictions
    best_model = xgb_model if r2_score(y_test, xgb_preds) > r2_score(y_test, rf_preds) else rf_model
    best_model_name = "XGBoost" if best_model == xgb_model else "Random Forest"
    print(f"\nUsing {best_model_name} to predict performance for all interns.")
    
    all_preds = best_model.predict(X_imputed)
    df['Predicted_Performance'] = all_preds
    
    # Define categories based on predicted performance
    # Let's say < 60 is Struggle, 60-80 is Average, > 80 is Excel
    df['Prediction_Category'] = pd.cut(df['Predicted_Performance'], 
                                       bins=[-np.inf, 60, 80, np.inf], 
                                       labels=['Struggle', 'Average', 'Excel'])
    
    print("\nCategory Distribution:")
    print(df['Prediction_Category'].value_counts())
    
    # Save the output
    output_file = 'intern_predictions.csv'
    df.to_csv(output_file, index=False)
    print(f"\nPredictions saved to {output_file}")
    
    # Save model and imputer
    joblib.dump(best_model, 'xgboost_model.pkl')
    joblib.dump(imputer, 'imputer.pkl')
    print("Model and imputer saved to .pkl files.")

if __name__ == "__main__":
    main()
