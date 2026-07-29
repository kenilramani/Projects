import pandas as pd
import numpy as np
# from prophet import Prophet
import matplotlib.pyplot as plt
import multiprocessing as mp

class cleanData():
    def __init__(self,dataframe):
        self.data_df = dataframe
        self.data_df['invoiceDate'] = pd.to_datetime(self.data_df['invoiceDate'].astype(str), format='%m/%d/%Y', errors='coerce')

    def filter_productsby(self, productId=None, customerType=None):
        if productId is not None:
            if not isinstance(productId, list):
                productId = [productId]

            self.data_df = self.data_df[self.data_df['productId'].isin(productId)]

        if customerType is not None:
            if not isinstance(customerType, list):
                customerType = [customerType]

            for ct in customerType:
                if ct not in ['stockist', 'chemist']:
                    raise ValueError("customerType must be either 'stockist', 'chemist', or a list of them")

            condition = pd.Series([False] * len(self.data_df), index=self.data_df.index)

            if 'stockist' in customerType:
                condition = condition | self.data_df['stockistId'].notna()

            if 'chemist' in customerType:
                condition = condition | self.data_df['chemistId'].notna()

            self.data_df = self.data_df[condition]

        self.data_df['salesYear'] = pd.to_datetime(self.data_df['salesYear'].astype(str), format='%Y', errors='coerce').dt.year
        self.data_df = self.data_df.sort_values(by='invoiceDate')

    def group_by_frequency(frequency):
        allowed_values = {'daily', 'weekly', 'weekly_monday', 'monthly','monthly_first', 'yearly'}
        if frequency not in allowed_values:
            raise ValueError(f"Invalid frequency '{frequency}'. Must be one of: {', '.join(allowed_values)}")
        else:
            return frequency
        
    def aggregate_sales(self,frequency):
        # frequency = group_by_frequency(frequency)
        allowed_values = {'daily', 'weekly', 'weekly_monday', 'monthly','monthly_first', 'yearly'}
        if frequency not in allowed_values:
            raise ValueError(f"Invalid frequency '{frequency}'. Must be one of: {', '.join(allowed_values)}")
        else:
            if frequency == 'daily':
                self.data_df = self.data_df.groupby(['invoiceDate','salesYear','InvoiceWeek']).aggregate(
                    {
                        'qty': 'sum',
                        'amount': 'sum',
                        'rate' : 'mean'
                    }
                ).reset_index()
                # return df        
        #-----------------------------------------------------------------------------------
            if frequency == 'weekly_monday':
                # print(f'aggregating on weekly_monday')
                # print(f"hereeee {df['invoiceDate'].dt.weekday}")
                    # df['invoiceDate'] = df['invoiceDate'] - pd.to_timedelta(5 - df['invoiceDate'].dt.weekday, unit='D')
                days_to_subtract = (self.data_df['invoiceDate'].dt.weekday + 1) % 7
                self.data_df['invoiceDate'] = self.data_df['invoiceDate'] - pd.to_timedelta(days_to_subtract, unit='D')

                self.data_df = self.data_df.groupby('invoiceDate', as_index=True).aggregate(
                    {
                        'qty' : 'sum',
                        'amount' : 'sum',
                        'rate' : 'mean'
                    }
                ).reset_index()
                # return df
        #-----------------------------------------------------------------------------------
            if frequency == 'weekly':
                self.data_df = self.data_df.groupby(['salesYear','InvoiceWeek']).aggregate(
                    {
                        'qty' : 'sum',
                        'amount' : 'sum',
                        'rate' : 'mean',
                        'invoiceDate' : 'first'
                    }
                ).reset_index()
                # return df
        #-----------------------------------------------------------------------------------
            if frequency == 'monthly':
                # self.data_df['invoiceDate'] = pd.to_datetime(self.data_df['invoiceDate'])
                self.data_df['month_start'] = self.data_df['invoiceDate'].values.astype('datetime64[M]')

                self.data_df = self.data_df.groupby('month_start').agg({
                    'qty': 'sum',
                    'amount': 'sum',
                    'rate' : 'mean'
                }).reset_index()

                self.data_df.rename(columns={'month_start': 'invoiceDate'}, inplace=True)

        #-----------------------------------------------------------------------------------
            if frequency == 'monthly_first':
                self.data_df = self.data_df.groupby(['salesYear','salesMonth']).aggregate(
                    {
                        'qty' : 'sum',
                        'amount' : 'sum',
                        'rate' : 'mean'
                        # 'invoiceDate' : 'first'
                    }
                ).reset_index()
                # return df
            if frequency == 'yearly':
                self.data_df['year_start'] = pd.to_datetime(self.data_df['invoiceDate'].values.astype('datetime64[Y]'))
                self.data_df = self.data_df.groupby(['year_start']).aggregate(
                    {
                        'qty': 'sum',
                        'amount': 'sum',
                        'rate' : 'mean'
                    }
                ).reset_index()            
                self.data_df.rename(columns={'year_start': 'invoiceDate'}, inplace=True)
                # return df


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
        else:
            raise ValueError("Invalid strategy. Choose from 'cap', 'nan', 'remove_rows', 'identify_only'.")
        # cleaned_df = df_processed[(df_processed[column] >= lower_bound) & (df_processed[column] <= upper_bound)]
        # return df_processed,outliers
