import streamlit as st
from main import InventorySystem
import pandas as pd

# Initialize Streamlit app
st.title("Mini Inventory Management System")

# Initialize InventorySystem
try:
    inventory = InventorySystem()
except Exception as e:
    st.error(f"Failed to connect to databases: {str(e)}")
    st.stop()

# Sidebar for navigation
st.sidebar.title("Operations")
operation = st.sidebar.selectbox(
    "Select Operation",
    [
        "Add Category",
        "Add Supplier",
        "View Categories",
        "View Suppliers",
        "Add Product",
        "Retrieve Product by ID",
        "Retrieve by Price Range",
        "List All Products",
        "Update Product Price",
        "Update Stock Quantity",
        "Delete Product",
        "View Shard Counts"
    ]
)

# Add Category
if operation == "Add Category":
    st.header("Add New Category")
    with st.form("add_category_form"):
        category_id = st.number_input("Category ID", min_value=1, step=1)
        category_name = st.text_input("Category Name")
        submit = st.form_submit_button("Add Category")

        if submit:
            if category_id > 0 and category_name:
                try:
                    success = inventory.add_category(category_id, category_name)
                    if success:
                        st.success(f"Category '{category_name}' added successfully with ID: {category_id}")
                except Exception as e:
                    st.error(f"Error adding category: {str(e)}")
            else:
                st.error("Please provide a valid Category ID and Name.")

# Add Supplier
elif operation == "Add Supplier":
    st.header("Add New Supplier")
    with st.form("add_supplier_form"):
        supplier_id = st.number_input("Supplier ID", min_value=1, step=1)
        supplier_name = st.text_input("Supplier Name")
        contact_info = st.text_input("Contact Info (e.g., email)")
        submit = st.form_submit_button("Add Supplier")

        if submit:
            if supplier_id > 0 and supplier_name:
                try:
                    success = inventory.add_supplier(supplier_id, supplier_name, contact_info)
                    if success:
                        st.success(f"Supplier '{supplier_name}' added successfully with ID: {supplier_id}")
                except Exception as e:
                    st.error(f"Error adding supplier: {str(e)}")
            else:
                st.error("Please provide a valid Supplier ID and Name.")

# View Categories
elif operation == "View Categories":
    st.header("List of Categories")
    if st.button("Load Categories"):
        try:
            categories = inventory.get_all_categories()
            if categories:
                df = pd.DataFrame(categories)
                st.write("**Categories:**")
                st.dataframe(df)
            else:
                st.warning("No categories found.")
        except Exception as e:
            st.error(f"Error retrieving categories: {str(e)}")

# View Suppliers
elif operation == "View Suppliers":
    st.header("List of Suppliers")
    if st.button("Load Suppliers"):
        try:
            suppliers = inventory.get_all_suppliers()
            if suppliers:
                df = pd.DataFrame(suppliers)
                st.write("**Suppliers:**")
                st.dataframe(df)
            else:
                st.warning("No suppliers found.")
        except Exception as e:
            st.error(f"Error retrieving suppliers: {str(e)}")

# Add Product
elif operation == "Add Product":
    st.header("Add New Product")
    categories = inventory.get_all_categories()
    suppliers = inventory.get_all_suppliers()

    if not categories or not suppliers:
        st.warning("Please add at least one category and supplier before adding a product.")
    else:
        category_options = {f"{cat['CategoryID']}: {cat['CategoryName']}": cat['CategoryID'] for cat in categories}
        supplier_options = {f"{sup['SupplierID']}: {sup['SupplierName']}": sup['SupplierID'] for sup in suppliers}

        with st.form("add_product_form"):
            name = st.text_input("Product Name")
            description = st.text_area("Description")
            price = st.number_input("Price", min_value=0.01, step=0.01)
            stock_quantity = st.number_input("Stock Quantity", min_value=0, step=1)
            category_selection = st.selectbox("Select Category", list(category_options.keys()))
            supplier_selection = st.selectbox("Select Supplier", list(supplier_options.keys()))
            submit = st.form_submit_button("Add Product")

            if submit:
                if name and price > 0 and stock_quantity >= 0:
                    try:
                        category_id = category_options[category_selection]
                        supplier_id = supplier_options[supplier_selection]
                        product_id = inventory.add_product(
                            name, description, price, stock_quantity, category_id, supplier_id
                        )
                        st.success(f"Product added successfully with ID: {product_id}")
                    except Exception as e:
                        st.error(f"Error adding product: {str(e)}")
                else:
                    st.error("Please fill in all required fields with valid values.")

# Retrieve Product by ID
elif operation == "Retrieve Product by ID":
    st.header("Retrieve Product by ID")
    product_id = st.text_input("Enter Product ID (UUID)")
    if st.button("Retrieve"):
        if product_id:
            try:
                product = inventory.get_product_by_id(product_id)
                if product:
                    st.write("**Product Details:**")
                    st.json(product)
                else:
                    st.warning("Product not found.")
            except Exception as e:
                st.error(f"Error retrieving product: {str(e)}")
        else:
            st.error("Please enter a valid Product ID.")

# Retrieve by Price Range
elif operation == "Retrieve by Price Range":
    st.header("Retrieve Products by Price Range")
    min_price = st.number_input("Minimum Price", min_value=0.0, step=0.01)
    max_price = st.number_input("Maximum Price", min_value=0.0, step=0.01)
    if st.button("Retrieve"):
        if min_price <= max_price:
            try:
                products = inventory.get_products_by_price_range(min_price, max_price)
                if products:
                    df = pd.DataFrame(products)
                    st.write("**Products Found:**")
                    st.dataframe(df)
                else:
                    st.warning("No products found in the specified price range.")
            except Exception as e:
                st.error(f"Error retrieving products: {str(e)}")
        else:
            st.error("Minimum price must be less than or equal to maximum price.")

# List All Products
elif operation == "List All Products":
    st.header("List All Products")
    if st.button("Load Products"):
        try:
            products = inventory.list_all_products()
            if products:
                df = pd.DataFrame(products)
                st.write("**All Products:**")
                st.dataframe(df)
            else:
                st.warning("No products found across all shards.")
        except Exception as e:
            st.error(f"Error listing products: {str(e)}")

# Update Product Price
elif operation == "Update Product Price":
    st.header("Update Product Price")
    with st.form("update_price_form"):
        product_id = st.text_input("Product ID (UUID)")
        new_price = st.number_input("New Price", min_value=0.01, step=0.01)
        submit = st.form_submit_button("Update Price")

        if submit:
            if product_id and new_price > 0:
                try:
                    success = inventory.update_product_price(product_id, new_price)
                    if success:
                        st.success("Price updated successfully.")
                    else:
                        st.warning("Product not found.")
                except Exception as e:
                    st.error(f"Error updating price: {str(e)}")
            else:
                st.error("Please provide a valid Product ID and price.")

# Update Stock Quantity
elif operation == "Update Stock Quantity":
    st.header("Update Stock Quantity")
    with st.form("update_stock_form"):
        product_id = st.text_input("Product ID (UUID)")
        quantity_change = st.number_input("Quantity Change (Positive to add, Negative to subtract)", step=1)
        submit = st.form_submit_button("Update Stock")

        if submit:
            if product_id:
                try:
                    success = inventory.update_stock_quantity(product_id, quantity_change)
                    if success:
                        st.success("Stock quantity updated successfully.")
                    else:
                        st.warning("Product not found.")
                except Exception as e:
                    st.error(f"Error updating stock: {str(e)}")
            else:
                st.error("Please provide a valid Product ID.")

# Delete Product
elif operation == "Delete Product":
    st.header("Delete Product")
    product_id = st.text_input("Enter Product ID (UUID)")
    if st.button("Delete"):
        if product_id:
            try:
                success = inventory.delete_product(product_id)
                if success:
                    st.success("Product deleted successfully.")
                else:
                    st.warning("Product not found.")
            except Exception as e:
                st.error(f"Error deleting product: {str(e)}")
        else:
            st.error("Please enter a valid Product ID.")

# View Shard Counts
elif operation == "View Shard Counts":
    st.header("Shard Product Counts")
    if st.button("Load Shard Counts"):
        try:
            counts = inventory.get_shard_counts()
            df = pd.DataFrame.from_dict(counts, orient='index', columns=['Product Count'])
            st.write("**Products per Shard:**")
            st.dataframe(df)
        except Exception as e:
            st.error(f"Error retrieving shard counts: {str(e)}")