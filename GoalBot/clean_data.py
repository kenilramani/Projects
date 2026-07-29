import pandas as pd
import numpy as np
# from prophet import Prophet
import matplotlib.pyplot as plt
import multiprocessing as mp

class cleanData():
    def __init__(self,dataframe):
        self.data_df = dataframe.copy()
        self.data_df['productId'] = self.data_df['productId'].astype(int)

        if not np.issubdtype(self.data_df['invoiceDate'].dtype, np.datetime64):
            self.data_df['invoiceDate'] = pd.to_datetime(self.data_df['invoiceDate'])

        # if self.data_df['invoiceDate'].dtype == object:
        #     self.data_df['invoiceDate'] = pd.to_datetime(self.data_df['invoiceDate'].astype(str), format='%m/%d/%Y', errors='coerce')

    # def filter_productsby(self, product_ids, customer_type):
    #     # Validate input types
    #     if not isinstance(product_ids, list):
    #         raise TypeError("product_ids must be a list")

    #     if customer_type not in ['stockist', 'chemist']:
    #         raise ValueError("customer_type must be either 'stockist' or 'chemist'")

    #     # Filter by product IDs
    #     self.data_df = self.data_df[self.data_df['productId'].isin(product_ids)]

    #     # Filter by customer type
    #     if customer_type == 'stockist':
    #         self.data_df = self.data_df[self.data_df['stockistId'].notna()]
    #         self.data_df = self.data_df.drop(columns=['chemistId'], errors='ignore')
    #     else:  # customer_type == 'chemist'
    #         self.data_df = self.data_df[self.data_df['chemistId'].notna()]
    #         self.data_df = self.data_df.drop(columns=['stockistId'], errors='ignore')

    #     # Date conversions
    #     self.data_df['invoiceDate'] = pd.to_datetime(self.data_df['invoiceDate'], errors='coerce')
    #     self.data_df['salesYear'] = pd.to_datetime(self.data_df['salesYear'].astype(str), format='%Y', errors='coerce').dt.year

    #     # Sort by invoiceDate
    #     self.data_df = self.data_df.sort_values(by='invoiceDate')

    # def filter_productsby(self,productId,customerType = None):

    #     # filter product 
    #     self.data_df = self.data_df[self.data_df['productId'] == productId]

    #     if customerType is None:
    #         pass
    #     elif customerType not in ['stockist','chemist']:
    #         raise ValueError("customerType must be either 'stockist' or 'chemist'")
    #     elif customerType == 'stockist':
    #         # filter stockist
    #         self.data_df = self.data_df[self.data_df['stockistId'].isna() == False]
    #         # self.data_df = self.data_df[self.data_df['stockistId'].isna() == False].drop(columns=['chemistId'],axis=1)
    #     elif customerType == 'chemist':
    #         # filter chemist
    #         self.data_df = self.data_df[self.data_df['stockistId'].isna() == False]
    #         # self.data_df = self.data_df[self.data_df['chemistId'].isna() == False].drop(columns=['stockistId'],axis=1)

    #     self.data_df['invoiceDate'] = pd.to_datetime(self.data_df['invoiceDate'].astype(str), format='%m/%d/%Y')
    #     self.data_df['salesYear'] = pd.to_datetime(self.data_df['salesYear'].astype(str), format='%Y').dt.year
    #     self.data_df = self.data_df.sort_values(by='invoiceDate')

    # def filter_productsby(self, productId=None, customerType=None):
    #     """
    #     Filters the data by one or more productIds and optionally by customerType ('stockist' or 'chemist').

    #     Parameters:
    #     - productId: int, str, or list of them
    #     - customerType: str or list of str (optional)
    #     """
    #     if productId is not None:
    #         if not isinstance(productId, list):
    #             productId = [productId]

    #         self.data_df = self.data_df[self.data_df['productId'].isin(productId)]

    #     # Filter by customerType if provided
    #     if customerType is not None:
    #         if not isinstance(customerType, list):
    #             customerType = [customerType]

    #         for ct in customerType:
    #             if ct not in ['stockist', 'chemist']:
    #                 raise ValueError("customerType must be either 'stockist', 'chemist', or a list of them")

    #         # Apply filtering for customer types
    #         condition = pd.Series([False] * len(self.data_df), index=self.data_df.index)

    #         if 'stockist' in customerType:
    #             condition = condition | self.data_df['stockistId'].notna()

    #         if 'chemist' in customerType:
    #             condition = condition | self.data_df['chemistId'].notna()

    #         self.data_df = self.data_df[condition]

    #     # Date parsing and sorting
    #     self.data_df['year'] = pd.to_datetime(self.data_df['year'].astype(str), format='%Y', errors='coerce').dt.year
    #     self.data_df = self.data_df.sort_values(by='invoiceDate')

    def filter_productsby(self, productId=None, customerType=None):
        """
        Returns a filtered DataFrame by one or more productIds and optionally by customerType ('stockist' or 'chemist').

        Parameters:
        - productId: int, str, or list of them
        - customerType: str or list of str (optional)
        """
        df = self.data_df.copy()

        if productId is not None:
            if not isinstance(productId, list):
                productId = [productId]
            df = df[df['productId'].isin(productId)]

        # Filter by customerType if provided
        if customerType is not None:
            if not isinstance(customerType, list):
                customerType = [customerType]

            for ct in customerType:
                if ct not in ['stockist', 'chemist']:
                    raise ValueError("customerType must be either 'stockist', 'chemist', or a list of them")

            condition = pd.Series([False] * len(df), index=df.index)

            if 'stockist' in customerType:
                condition = condition | df['stockistId'].notna()

            if 'chemist' in customerType:
                condition = condition | df['chemistId'].notna()

            df = df[condition]

        # Date parsing and sorting
        # df['year'] = pd.to_datetime(df['year'].astype(str), format='%Y', errors='coerce').dt.year
        # df = df.sort_values(by='invoiceDate')

        return df

    def group_by_frequency(frequency):
        allowed_values = {'daily', 'weekly', 'weekly_monday', 'monthly', 'monthly_first', 'yearly'}
        if frequency not in allowed_values:
            raise ValueError(f"Invalid frequency '{frequency}'. Must be one of: {', '.join(allowed_values)}")
        else:
            return frequency
       

    def aggregate_sales(self, frequency, productId=None):
        """
        Returns a new DataFrame aggregated by the specified frequency, keeping self.data_df unchanged.
        """

        if productId is not None:
            df = self.filter_productsby(productId=productId)
        else:
            df = self.data_df.copy()

        allowed_values = {'daily', 'weekly', 'weekly_monday', 'monthly', 'yearly'}     # 'monthly_first'
        if frequency not in allowed_values:
            raise ValueError(f"Invalid frequency '{frequency}'. Must be one of: {', '.join(allowed_values)}")

        # df = self.data_df.copy()

        if frequency == 'daily':
            df = df.groupby(['invoiceDate']).aggregate(
                {
                    # 'qty': 'sum',
                    'amount': 'sum',
                    # 'free': 'sum',
                    # 'rate' : 'mean'
                }
            ).reset_index()
            return df

        if frequency == 'weekly_monday':
            days_to_subtract = (df['invoiceDate'].dt.weekday) % 7
            df['invoiceDate'] = df['invoiceDate'] - pd.to_timedelta(days_to_subtract, unit='D')
            df = df.groupby('invoiceDate', as_index=True).aggregate(
                {
                    # 'qty': 'sum',
                    'amount': 'sum',
                    # 'free': 'sum',
                    # 'rate' : 'mean'
                }
            ).reset_index()
            return df

        ## Gives only 53 rows.
        # if frequency == 'weekly':
        #     df = df.groupby(['week_of_year']).aggregate(
        #         {
        #             # 'qty': 'sum',
        #             'amount': 'sum',
        #             'invoiceDate': 'first',
        #             # 'rate' : 'mean'
        #         }
        #     ).reset_index()
        #     return df

        if frequency == 'weekly':
            df['year'] = df['invoiceDate'].dt.isocalendar().year
            df['week'] = df['invoiceDate'].dt.isocalendar().week

            df = df.groupby(['year', 'week'], as_index=False).aggregate({
                'amount': 'sum',
                'invoiceDate': 'first',
            })

            return df


        if frequency == 'monthly':
            df['month_start'] = df['invoiceDate'].values.astype('datetime64[M]')
            df = df.groupby('month_start').agg({
                # 'qty': 'sum',
                'amount': 'sum'
            }).reset_index()
            df.rename(columns={'month_start': 'invoiceDate'}, inplace=True)
            return df

        #  Getting error--> KeyError: 'salesYear'
        # if frequency == 'monthly_first':
        #     df = df.groupby(['salesYear', 'salesMonth']).aggregate(
        #         {
        #             # 'qty': 'sum',
        #             'amount': 'sum',
        #             # 'invoiceDate' : 'first'
        #         }
        #     ).reset_index()
        #     return df

        if frequency == 'yearly':
            df['year_start'] = pd.to_datetime(df['invoiceDate'].values.astype('datetime64[Y]'))
            df = df.groupby(['year_start']).aggregate(
                {
                    'qty': 'sum',
                    'amount': 'sum',
                }
            ).reset_index()
            df.rename(columns={'year_start': 'invoiceDate'}, inplace=True)
            return df
        
    def create_time_features(self, productId, frequency='daily', ):
        df1 = self.aggregate_sales(frequency,productId)

        df = self.fill_missing_dates(df1)
        
        df['invoiceDate'] = pd.to_datetime(df['invoiceDate'])
        
        df['year'] = df['invoiceDate'].dt.year
        df['month'] = df['invoiceDate'].dt.month
        df['day'] = df['invoiceDate'].dt.day
        df['day_of_week'] = df['invoiceDate'].dt.dayofweek  # Monday=0, Sunday=6
        df['day_of_year'] = df['invoiceDate'].dt.dayofyear
        df['week_of_year'] = df['invoiceDate'].dt.isocalendar().week.astype(int)
        df['quarter'] = df['invoiceDate'].dt.quarter

        # Weekend indicator
        df['is_weekend'] = (df['day_of_week'].isin([5, 6])).astype(int)

        # Binary/Cyclical features
        df['is_month_start'] = df['invoiceDate'].dt.is_month_start.astype(int)
        df['is_month_end'] = df['invoiceDate'].dt.is_month_end.astype(int)
        df['is_quarter_start'] = df['invoiceDate'].dt.is_quarter_start.astype(int)
        df['is_quarter_end'] = df['invoiceDate'].dt.is_quarter_end.astype(int)
        df['is_year_start'] = df['invoiceDate'].dt.is_year_start.astype(int)
        df['is_year_end'] = df['invoiceDate'].dt.is_year_end.astype(int)
        
        # Trend feature
        df['trend'] = np.arange(len(df))
        df['trend_squared'] = df['trend'] ** 2
        df['trend_log'] = np.log(df['trend'] + 1)
        
        # Lag features (autoregression)
        lags = [7, 14, 21, 28, 90, 180, 270, 365] # Weekly, bi-weekly, tri-weekly, monthly, yearly lags
        for lag in lags:
            df[f'lag_{lag}'] = df['amount'].shift(lag)
            
        # Rolling window features (momentum)
        windows = [7, 14, 21, 28, 90, 180, 270, 365]
        for window in windows:
            df[f'rolling_mean_{window}'] = df['amount'].shift(1).rolling(window=window).mean()
            df[f'rolling_std_{window}'] = df['amount'].shift(1).rolling(window=window).std()

        # df = df.drop('date', axis=1)
        return df

    def process_outliers(self,column,multiplier=1.5,q1=0.25, q3=0.75,strategy='cap'):
        # df_processed = df.copy()
        # print("in calculate_iqr")

        Q1 = self.data_df[column].quantile(q1)
        Q3 = self.data_df[column].quantile(q3)
        IQR = Q3 - Q1
        # print(IQR)

        lower_bound = Q1 - multiplier * IQR
        upper_bound = Q3 + multiplier * IQR

        print(f"{column} ---> Q1: {Q1}, Q3: {Q3}, IQR: {IQR}")
        print(f"Lower Bound: {lower_bound}, Upper Bound: {upper_bound}")

        outliers_condition = (self.data_df[column] < lower_bound) | (self.data_df[column] > upper_bound)
        outliers = self.data_df[outliers_condition]

        if strategy == 'cap':
            self.data_df[column] = self.data_df[column].clip(lower=lower_bound, upper=upper_bound)
            print(f"Outliers in '{column}' have been capped.")
        elif strategy == 'nan':
            self.data_df.loc[outliers_condition, column] = np.nan
            print(f"Outliers in '{column}' have been replaced with NaN.")
        elif strategy == 'remove_rows':
            self.data_df = self.data_df[~outliers_condition]
            print(f"Rows with outliers in '{column}' have been removed.")
        elif strategy == 'identify_only':
            print(f"Outliers in '{column}' identified. No changes made to the DataFrame structure.")
            # In this case, df_processed is still the original (copied) df
        else:
            raise ValueError("Invalid strategy. Choose from 'cap', 'nan', 'remove_rows', 'identify_only'.")
        # cleaned_df = df_processed[(df_processed[column] >= lower_bound) & (df_processed[column] <= upper_bound)]
        # return df_processed,outliers

    def plot_predicted_vs_actual(predicted, actual, feature):        
        plt.figure(figsize=(10, 5))
        
        if not predicted.empty:
            plt.plot(predicted['invoiceDate'], predicted[feature], marker='.', linestyle='', color='green')
        if not actual.empty:
            plt.plot(actual['invoiceDate'], actual[feature], marker='.', linestyle='', color='red')

        plt.title(f'Data Points of {feature}')
        plt.xlabel('invoiceDate')
        plt.ylabel(f'{feature}')
        plt.legend(['predicted', 'actual'])
        plt.grid(True)
        plt.xticks(rotation=45)  # Optional: for better date visibility
        plt.tight_layout()
        plt.show()


def fill_missing_dates(dataframe, date_col='invoiceDate', freq='D',fillna=True, epsilon = np.finfo(float).eps):
    df = dataframe.copy()
    
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col])
        df.set_index(date_col, inplace=True)
    else:
        df.index = pd.to_datetime(df.index)
    
    full_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq=freq)
    
    df_filled = df.reindex(full_range)
    df_filled.index.name = date_col
    
    if fillna is True:
        df_filled=df_filled.fillna(epsilon)

    df_filled = df_filled.reset_index()

    return df_filled

# def fill_missing_dates(dataframe, date_col='invoiceDate', freq='D', fillna=True, epsilon=np.finfo(float).eps):
#     df = dataframe.copy()

#     if date_col in df.columns:
#         df[date_col] = pd.to_datetime(df[date_col])
#         df = df.sort_values(by=date_col)
#         df[date_col] += pd.to_timedelta(df.groupby(date_col).cumcount(), unit='s')  # ✅ Modify to avoid duplicates
#         df.set_index(date_col, inplace=True)
#     else:
#         df.index = pd.to_datetime(df.index)
#         df = df.sort_index()
#         df.index += pd.to_timedelta(df.groupby(df.index).cumcount(), unit='s')  # ✅ For datetime index

#     full_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq=freq)

#     df_filled = df.reindex(full_range)
#     df_filled.index.name = date_col

#     if fillna:
#         df_filled = df_filled.fillna(epsilon)

#     df_filled = df_filled.reset_index()

#     return df_filled


def create_time_features(df):
    
    df['invoiceDate'] = pd.to_datetime(df['invoiceDate'])
    
    df['year'] = df['invoiceDate'].dt.year
    df['month'] = df['invoiceDate'].dt.month
    df['day'] = df['invoiceDate'].dt.day
    df['day_of_week'] = df['invoiceDate'].dt.dayofweek  # Monday=0, Sunday=6
    df['day_of_year'] = df['invoiceDate'].dt.dayofyear
    df['week_of_year'] = df['invoiceDate'].dt.isocalendar().week.astype(int)
    df['quarter'] = df['invoiceDate'].dt.quarter

    # Weekend indicator
    df['is_weekend'] = (df['day_of_week'].isin([5, 6])).astype(int)

    # Binary/Cyclical features
    df['is_month_start'] = df['invoiceDate'].dt.is_month_start.astype(int)
    df['is_month_end'] = df['invoiceDate'].dt.is_month_end.astype(int)
    df['is_quarter_start'] = df['invoiceDate'].dt.is_quarter_start.astype(int)
    df['is_quarter_end'] = df['invoiceDate'].dt.is_quarter_end.astype(int)
    df['is_year_start'] = df['invoiceDate'].dt.is_year_start.astype(int)
    df['is_year_end'] = df['invoiceDate'].dt.is_year_end.astype(int)
    
    # Trend feature
    df['trend'] = np.arange(len(df))
    df['trend_squared'] = df['trend'] ** 2
    df['trend_log'] = np.log(df['trend'] + 1)
    
    # df = df.drop('date', axis=1)
    return df

def create_amount_features(df):    
    # Lag features (autoregression)
    lags = [7, 14, 21, 28, 90, 180, 270, 365] # Weekly, bi-weekly, tri-weekly, monthly, yearly lags
    for lag in lags:
        df[f'lag_{lag}'] = df['amount'].shift(lag)
        
    # Rolling window features (momentum)
    windows = [7, 14, 21, 28, 90, 180, 270, 365]
    for window in windows:
        df[f'rolling_mean_{window}'] = df['amount'].shift(1).rolling(window=window).mean()
        df[f'rolling_std_{window}'] = df['amount'].shift(1).rolling(window=window).std()

    return df

def train_test_split_by_date(df, split_date='2024-01-01'):
    split_date = pd.to_datetime(split_date)
    
    train_data = df[df['invoiceDate'] < split_date].copy()
    test_data = df[df['invoiceDate'] >= split_date].copy()
    
    print(f"Training data: {len(train_data)} rows")
    print(f"Test data: {len(test_data)} rows")
    print(f"Training date range: {train_data['invoiceDate'].min()} to {train_data['invoiceDate'].max()}")
    print(f"Test date range: {test_data['invoiceDate'].min()} to {test_data['invoiceDate'].max()}")

    # xtrain = train_data
    
    return train_data, test_data