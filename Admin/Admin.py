from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.uix.modalview import ModalView
from kivy.lang import Builder
from collections import OrderedDict
from pymongo import MongoClient
from Admin.Utilities.data import DataTable
from datetime import datetime
import hashlib
import pandas as pd
import matplotlib.pyplot as plt
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg as MTP

Builder.load_file('Admin/Admin.kv')

class Notify(ModalView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (.7,.7)

class AdminWindow(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            client = MongoClient()
            db = client.Pos
            self.users = db.users
            self.products = db.stocks
            self.notify = Notify()

            product_code = []
            product_name = []
            spinvals = []
            for product in self.products.find():
                if 'product_code' not in product or 'product_name' not in product:
                    continue
                
                code = product.get('product_code', '')
                name = product.get('product_name', '')
                if len(name) > 30:
                    name = name[:30] + '...'
                
                product_code.append(code)
                product_name.append(name)
                spinvals.append(f"{code} | {name}")

            self.ids.target_product.values = spinvals

            # Display Users
            content = self.ids.scrn_contents
            users = self.get_users()
            userstable = DataTable(table=users)
            content.add_widget(userstable)

            # Display Products
            product_scrn = self.ids.scrn_product_contents
            products = self.get_products()
            prod_table = DataTable(table=products)
            product_scrn.add_widget(prod_table)

        except Exception as e:
            print(f"Error initializing AdminWindow: {str(e)}")
            self.notify.add_widget(Label(text=f'[color=#FF0000][b]Database Error: {str(e)}[/b][/color]', markup=True))
            self.notify.open()
            Clock.schedule_once(self.killswitch, 3)

    def add_user_fields(self):
        target = self.ids.ops_fields
        target.clear_widgets()
        crud_first = TextInput(hint_text='First Name', multiline=False)
        crud_last = TextInput(hint_text='Last Name', multiline=False)
        crud_user = TextInput(hint_text='User Name', multiline=False)
        crud_pwd = TextInput(hint_text='Password', multiline=False)
        crud_des = Spinner(text='Operator', values=['Operator', 'Administrator'])
        crud_submit = Button(
            text='Add', size_hint_x=None, width=100,
            on_release=lambda x: self.add_user(
                crud_first.text, crud_last.text, 
                crud_user.text, crud_pwd.text, 
                crud_des.text
            )
        )

        target.add_widget(crud_first)
        target.add_widget(crud_last)
        target.add_widget(crud_user)
        target.add_widget(crud_pwd)
        target.add_widget(crud_des)
        target.add_widget(crud_submit)
    
    def add_product_fields(self):
        target = self.ids.ops_fields_p
        target.clear_widgets()

        crud_code = TextInput(hint_text='Product Code', multiline=False)
        crud_name = TextInput(hint_text='Product Name', multiline=False)
        crud_weight = TextInput(hint_text='Product Weight', multiline=False)
        crud_stock = TextInput(hint_text='Product In Stock', multiline=False)
        crud_sold = TextInput(hint_text='Products Sold', multiline=False)
        crud_barcode_number = TextInput(hint_text='Barcode Number', multiline=False)
        crud_purchase = TextInput(hint_text='Last Purchase', multiline=False)
        crud_submit = Button(
            text='Add', size_hint_x=None, width=100,
            on_release=lambda x: self.add_product(
                crud_code.text, crud_name.text, 
                crud_weight.text, crud_stock.text, 
                crud_sold.text, crud_barcode_number.text, 
                crud_purchase.text
            )
        )

        target.add_widget(crud_code)
        target.add_widget(crud_name)
        target.add_widget(crud_weight)
        target.add_widget(crud_stock)
        target.add_widget(crud_sold)
        target.add_widget(crud_barcode_number)
        target.add_widget(crud_purchase)
        target.add_widget(crud_submit)

    def add_user(self, first, last, user, pwd, des):
        try:
            if not all([first, last, user, pwd]):
                self.show_error("All fields are required")
                return

            pwd = hashlib.sha256(pwd.encode()).hexdigest()
            self.users.insert_one({
                'first_name': first,
                'last_name': last,
                'user_name': user,
                'password': pwd,
                'designation': des,
                'date': datetime.now()
            })
            
            self.refresh_users_table()
            
        except Exception as e:
            self.show_error(f"Error adding user: {str(e)}")

    def add_product(self, code, name, weight, stock, sold, barcode_number, purchase):
        try:
            if not all([code, name, weight, stock, barcode_number]):
                self.show_error("Required fields: code, name, weight, stock, barcode")
                return

            self.products.insert_one({
                'product_code': code,
                'product_name': name,
                'product_weight': weight,
                'in_stock': stock,
                'sold': sold,
                'barcode_number': barcode_number,
                'last_purchase': purchase
            })
            
            self.refresh_products_table()
            
        except Exception as e:
            self.show_error(f"Error adding product: {str(e)}")

    def show_error(self, message):
        self.notify.add_widget(Label(text=f'[color=#FF0000][b]{message}[/b][/color]', markup=True))
        self.notify.open()
        Clock.schedule_once(self.killswitch, 2)

    def killswitch(self, dt):
        self.notify.dismiss()
        self.notify.clear_widgets()

    def refresh_users_table(self):
        content = self.ids.scrn_contents
        content.clear_widgets()
        users = self.get_users()
        userstable = DataTable(table=users)
        content.add_widget(userstable)

    def refresh_products_table(self):
        content = self.ids.scrn_product_contents
        content.clear_widgets()
        products = self.get_products()
        prod_table = DataTable(table=products)
        content.add_widget(prod_table)

    def update_user_fields(self):
        target = self.ids.ops_fields
        target.clear_widgets()
        crud_user = TextInput(hint_text='User Name to Update', multiline=False)
        crud_first = TextInput(hint_text='New First Name', multiline=False)
        crud_last = TextInput(hint_text='New Last Name', multiline=False)
        crud_pwd = TextInput(hint_text='New Password', multiline=False)
        crud_des = Spinner(text='Operator', values=['Operator', 'Administrator'])
        crud_submit = Button(
            text='Update', size_hint_x=None, width=100,
            on_release=lambda x: self.update_user(
                crud_user.text, crud_first.text, 
                crud_last.text, crud_pwd.text, 
                crud_des.text
            )
        )

        target.add_widget(crud_user)
        target.add_widget(crud_first)
        target.add_widget(crud_last)
        target.add_widget(crud_pwd)
        target.add_widget(crud_des)
        target.add_widget(crud_submit)

    def update_product_fields(self):
        target = self.ids.ops_fields_p
        target.clear_widgets()

        crud_code = TextInput(hint_text='Product Code to Update', multiline=False)
        crud_name = TextInput(hint_text='New Product Name', multiline=False)
        crud_weight = TextInput(hint_text='New Product Weight', multiline=False)
        crud_stock = TextInput(hint_text='New In Stock', multiline=False)
        crud_sold = TextInput(hint_text='New Sold', multiline=False)
        crud_barcode_number = TextInput(hint_text='New Barcode', multiline=False)
        crud_purchase = TextInput(hint_text='New Last Purchase', multiline=False)
        crud_submit = Button(
            text='Update', size_hint_x=None, width=100,
            on_release=lambda x: self.update_product(
                crud_code.text, crud_name.text, 
                crud_weight.text, crud_stock.text, 
                crud_sold.text, crud_barcode_number.text, 
                crud_purchase.text
            )
        )

        target.add_widget(crud_code)
        target.add_widget(crud_name)
        target.add_widget(crud_weight)
        target.add_widget(crud_stock)
        target.add_widget(crud_sold)
        target.add_widget(crud_barcode_number)
        target.add_widget(crud_purchase)
        target.add_widget(crud_submit)

    def update_user(self, user, first, last, pwd, des):
        try:
            if not user:
                self.show_error("Username is required")
                return

            target_user = self.users.find_one({'user_name': user})
            if not target_user:
                self.show_error("User not found")
                return

            update_data = {'date': datetime.now()}
            if first: update_data['first_name'] = first
            if last: update_data['last_name'] = last
            if pwd: update_data['password'] = hashlib.sha256(pwd.encode()).hexdigest()
            if des: update_data['designation'] = des

            self.users.update_one({'user_name': user}, {'$set': update_data})
            self.refresh_users_table()
            
        except Exception as e:
            self.show_error(f"Error updating user: {str(e)}")

    def update_product(self, code, name, weight, stock, sold, barcode_number, purchase):
        try:
            if not code:
                self.show_error("Product code is required")
                return

            target_product = self.products.find_one({'product_code': code})
            if not target_product:
                self.show_error("Product not found")
                return

            update_data = {}
            if name: update_data['product_name'] = name
            if weight: update_data['product_weight'] = weight
            if stock: update_data['in_stock'] = stock
            if sold: update_data['sold'] = sold
            if barcode_number: update_data['barcode_number'] = barcode_number
            if purchase: update_data['last_purchase'] = purchase

            self.products.update_one({'product_code': code}, {'$set': update_data})
            self.refresh_products_table()
            
        except Exception as e:
            self.show_error(f"Error updating product: {str(e)}")

    def remove_user_fields(self):
        target = self.ids.ops_fields
        target.clear_widgets()
        crud_user = TextInput(hint_text='User Name to Remove')
        crud_submit = Button(
            text='Remove', size_hint_x=None, width=100,
            on_release=lambda x: self.remove_user(crud_user.text)
        )

        target.add_widget(crud_user)
        target.add_widget(crud_submit)

    def remove_product_fields(self):
        target = self.ids.ops_fields_p
        target.clear_widgets()
        crud_code = TextInput(hint_text='Product Code to Remove')
        crud_submit = Button(
            text='Remove', size_hint_x=None, width=100,
            on_release=lambda x: self.remove_product(crud_code.text)
        )

        target.add_widget(crud_code)
        target.add_widget(crud_submit)

    def remove_user(self, user):
        try:
            if not user:
                self.show_error("Username is required")
                return

            target_user = self.users.find_one({'user_name': user})
            if not target_user:
                self.show_error("User not found")
                return

            self.users.delete_one({'user_name': user})
            self.refresh_users_table()
            
        except Exception as e:
            self.show_error(f"Error removing user: {str(e)}")

    def remove_product(self, code):
        try:
            if not code:
                self.show_error("Product code is required")
                return

            target_product = self.products.find_one({'product_code': code})
            if not target_product:
                self.show_error("Product not found")
                return

            self.products.delete_one({'product_code': code})
            self.refresh_products_table()
            
        except Exception as e:
            self.show_error(f"Error removing product: {str(e)}")

    def get_users(self):
        _users = OrderedDict()
        _users['first_names'] = {}
        _users['last_names'] = {}
        _users['user_names'] = {}
        _users['passwords'] = {}
        _users['designations'] = {}

        try:
            for idx, user in enumerate(self.users.find()):
                _users['first_names'][idx] = user.get('first_name', '')
                _users['last_names'][idx] = user.get('last_name', '')
                _users['user_names'][idx] = user.get('user_name', '')
                
                pwd = user.get('password', '')
                if len(pwd) > 10:
                    pwd = pwd[:10] + '...'
                _users['passwords'][idx] = pwd
                
                _users['designations'][idx] = user.get('designation', '')
                
        except Exception as e:
            print(f"Error getting users: {str(e)}")
            
        return _users

    def get_products(self):
        _stocks = OrderedDict()
        _stocks['product_code'] = {}
        _stocks['product_name'] = {}
        _stocks['product_weight'] = {}
        _stocks['in_stock'] = {}
        _stocks['sold'] = {}
        _stocks['barcode_number'] = {}
        _stocks['last_purchase'] = {}

        try:
            for idx, product in enumerate(self.products.find()):
                _stocks['product_code'][idx] = product.get('product_code', '')
                
                name = product.get('product_name', '')
                if len(name) > 10:
                    name = name[:10] + '...'
                _stocks['product_name'][idx] = name
                
                _stocks['product_weight'][idx] = product.get('product_weight', '')
                _stocks['in_stock'][idx] = product.get('in_stock', '')
                _stocks['sold'][idx] = product.get('sold', '')
                _stocks['barcode_number'][idx] = product.get('barcode_number', '')
                _stocks['last_purchase'][idx] = product.get('last_purchase', '')
                
        except Exception as e:
            print(f"Error getting products: {str(e)}")
            
        return _stocks

    def view_stats(self):
        try:
            plt.cla()
            self.ids.analysis_res.clear_widgets()
            
            target_product = self.ids.target_product.text
            if not target_product or ' | ' not in target_product:
                self.show_error("Please select a product")
                return
                
            target = target_product[:target_product.find(' | ')]
            name = target_product[target_product.find(' | ') + 3:]

            df = pd.read_csv("Admin/products_purchase.csv")
            purchases = []
            dates = []
            count = 0
            
            for x in range(len(df)):
                if str(df.Product_Code[x]) == target:
                    purchases.append(df.Purchased[x])
                    dates.append(count)
                    count += 1
                    
            if not purchases:
                self.show_error("No purchase data found")
                return
                
            plt.bar(dates, purchases, color='teal', label=name)
            plt.ylabel('Total Purchases')
            plt.xlabel('Day')
            plt.legend()

            self.ids.analysis_res.add_widget(MTP(plt.gcf()))
            
        except Exception as e:
            self.show_error(f"Error generating stats: {str(e)}")

    def change_screen(self, instance):
        if not instance.text:
            return
            
        if instance.text == 'Manage Products':
            self.ids.scrn_mngr.current = 'scrn_product_content'
        elif instance.text == 'Manage Users':
            self.ids.scrn_mngr.current = 'scrn_content'
        else:
            self.ids.scrn_mngr.current = 'scrn_analysis'

class AdminApp(App):
    def build(self):
        return AdminWindow()

if __name__ == '__main__':
    AdminApp().run()