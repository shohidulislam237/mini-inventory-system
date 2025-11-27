import mysql.connector
from typing import List, Dict, Optional
import uuid

# Configuration for MySQL databases (all within the same XAMPP MySQL instance)
DB_CONFIG = {
    'central': {'host': 'localhost', 'port': 3306, 'database': 'inventory_central', 'user': 'root', 'password': ''},
    'low_price': {'host': 'localhost', 'port': 3306, 'database': 'inventory_low', 'user': 'root', 'password': ''},
    'mid_price': {'host': 'localhost', 'port': 3306, 'database': 'inventory_mid', 'user': 'root', 'password': ''},
    'high_price': {'host': 'localhost', 'port': 3306, 'database': 'inventory_high', 'user': 'root', 'password': ''}
}

PRICE_RANGES = {
    'low_price': (0, 50),
    'mid_price': (50, 500),
    'high_price': (500, float('inf'))
}

class InventorySystem:
    def __init__(self):
        self.connections = {}
        for shard, config in DB_CONFIG.items():
            self.connections[shard] = mysql.connector.connect(**config)

    def get_shard_for_price(self, price: float) -> str:
        """Determine the appropriate shard based on price."""
        for shard, (min_price, max_price) in PRICE_RANGES.items():
            if min_price <= price < max_price:
                return shard
        raise ValueError("Price out of defined ranges")

    def add_category(self, category_id: int, category_name: str) -> bool:
        """Add a category to all shards."""
        try:
            for shard in ['low_price', 'mid_price', 'high_price']:
                conn = self.connections[shard]
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO Categories (CategoryID, CategoryName) VALUES (%s, %s)",
                        (category_id, category_name)
                    )
                conn.commit()
            return True
        except Exception as e:
            for shard in ['low_price', 'mid_price', 'high_price']:
                self.connections[shard].rollback()
            raise Exception(f"Failed to add category: {str(e)}")

    def add_supplier(self, supplier_id: int, supplier_name: str, contact_info: str) -> bool:
        """Add a supplier to all shards."""
        try:
            for shard in ['low_price', 'mid_price', 'high_price']:
                conn = self.connections[shard]
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO Suppliers (SupplierID, SupplierName, ContactInfo) VALUES (%s, %s, %s)",
                        (supplier_id, supplier_name, contact_info)
                    )
                conn.commit()
            return True
        except Exception as e:
            for shard in ['low_price', 'mid_price', 'high_price']:
                self.connections[shard].rollback()
            raise Exception(f"Failed to add supplier: {str(e)}")

    def get_all_categories(self) -> List[Dict]:
        """Retrieve all categories from one shard (since they are replicated)."""
        conn = self.connections['low_price']  # Any shard will do since data is replicated
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT CategoryID, CategoryName FROM Categories ORDER BY CategoryID")
            return cur.fetchall()

    def get_all_suppliers(self) -> List[Dict]:
        """Retrieve all suppliers from one shard (since they are replicated)."""
        conn = self.connections['low_price']  # Any shard will do since data is replicated
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT SupplierID, SupplierName FROM Suppliers ORDER BY SupplierID")
            return cur.fetchall()

    def add_product(self, name: str, description: str, price: float, stock_quantity: int, category_id: int, supplier_id: int) -> str:
        """Add a new product to the appropriate shard."""
        product_id = str(uuid.uuid4())
        shard = self.get_shard_for_price(price)
        conn = self.connections[shard]
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO Products (ProductID, ProductName, Description, Price, StockQuantity, CategoryID, SupplierID)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (product_id, name, description, price, stock_quantity, category_id, supplier_id)
                )
                with self.connections['central'].cursor() as cur_central:
                    cur_central.execute(
                        """INSERT INTO InventoryLogs (ProductID, ChangeType, QuantityChanged)
                        VALUES (%s, %s, %s)""",
                        (product_id, 'stock_in', stock_quantity)
                    )
            conn.commit()
            self.connections['central'].commit()
            return product_id
        except Exception as e:
            conn.rollback()
            self.connections['central'].rollback()
            raise Exception(f"Failed to add product: {str(e)}")

    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Retrieve a product by its globally unique ID."""
        for shard, conn in self.connections.items():
            if shard == 'central':
                continue
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    """SELECT p.*, c.CategoryName, s.SupplierName
                    FROM Products p
                    LEFT JOIN Categories c ON p.CategoryID = c.CategoryID
                    LEFT JOIN Suppliers s ON p.SupplierID = s.SupplierID
                    WHERE p.ProductID = %s""",
                    (product_id,)
                )
                result = cur.fetchone()
                if result:
                    return result
        return None

    def get_products_by_price_range(self, min_price: float, max_price: float) -> List[Dict]:
        """Retrieve products within a specified price range."""
        target_shards = []
        for shard, (shard_min, shard_max) in PRICE_RANGES.items():
            if min_price < shard_max and max_price > shard_min:
                target_shards.append(shard)

        results = []
        for shard in target_shards:
            conn = self.connections[shard]
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    """SELECT p.*, c.CategoryName, s.SupplierName
                    FROM Products p
                    LEFT JOIN Categories c ON p.CategoryID = c.CategoryID
                    LEFT JOIN Suppliers s ON p.SupplierID = s.SupplierID
                    WHERE p.Price >= %s AND p.Price < %s""",
                    (max(min_price, PRICE_RANGES[shard][0]), min(max_price, PRICE_RANGES[shard][1]))
                )
                results.extend(cur.fetchall())
        return results

    def list_all_products(self) -> List[Dict]:
        """Retrieve all products from all shards."""
        results = []
        for shard in ['low_price', 'mid_price', 'high_price']:
            conn = self.connections[shard]
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    """SELECT p.*, c.CategoryName, s.SupplierName
                    FROM Products p
                    LEFT JOIN Categories c ON p.CategoryID = c.CategoryID
                    LEFT JOIN Suppliers s ON p.SupplierID = s.SupplierID"""
                )
                results.extend(cur.fetchall())
        return results

    def update_product_price(self, product_id: str, new_price: float) -> bool:
        """Update a product's price, handling shard migration if necessary."""
        current_product = self.get_product_by_id(product_id)
        if not current_product:
            return False

        current_shard = self.get_shard_for_price(current_product['Price'])
        new_shard = self.get_shard_for_price(new_price)

        try:
            if current_shard != new_shard:
                with self.connections[new_shard].cursor() as cur_new:
                    cur_new.execute(
                        """INSERT INTO Products (ProductID, ProductName, Description, Price, StockQuantity, CategoryID, SupplierID)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                        (product_id, current_product['ProductName'], current_product['Description'],
                         new_price, current_product['StockQuantity'], current_product['CategoryID'],
                         current_product['SupplierID'])
                    )
                with self.connections[current_shard].cursor() as cur_old:
                    cur_old.execute("DELETE FROM Products WHERE ProductID = %s", (product_id,))
                self.connections[new_shard].commit()
                self.connections[current_shard].commit()
            else:
                with self.connections[current_shard].cursor() as cur:
                    cur.execute(
                        "UPDATE Products SET Price = %s, LastUpdated = NOW() WHERE ProductID = %s",
                        (new_price, product_id)
                    )
                self.connections[current_shard].commit()

            with self.connections['central'].cursor() as cur_central:
                cur_central.execute(
                    """INSERT INTO InventoryLogs (ProductID, ChangeType, QuantityChanged)
                    VALUES (%s, %s, %s)""",
                    (product_id, 'price_update', 0)
                )
            self.connections['central'].commit()
            return True
        except Exception as e:
            for shard in [current_shard, new_shard, 'central']:
                if shard in self.connections:
                    self.connections[shard].rollback()
            raise Exception(f"Failed to update price: {str(e)}")

    def update_stock_quantity(self, product_id: str, quantity_change: int) -> bool:
        """Update stock quantity for a product."""
        product = self.get_product_by_id(product_id)
        if not product:
            return False

        shard = self.get_shard_for_price(product['Price'])
        try:
            with self.connections[shard].cursor() as cur:
                cur.execute(
                    "UPDATE Products SET StockQuantity = StockQuantity + %s, LastUpdated = NOW() WHERE ProductID = %s",
                    (quantity_change, product_id)
                )
            with self.connections['central'].cursor() as cur_central:
                cur_central.execute(
                    """INSERT INTO InventoryLogs (ProductID, ChangeType, QuantityChanged)
                    VALUES (%s, %s, %s)""",
                    (product_id, 'stock_update', quantity_change)
                )
            self.connections[shard].commit()
            self.connections['central'].commit()
            return True
        except Exception as e:
            self.connections[shard].rollback()
            self.connections['central'].rollback()
            raise Exception(f"Failed to update stock: {str(e)}")

    def delete_product(self, product_id: str) -> bool:
        """Delete a product from its shard."""
        product = self.get_product_by_id(product_id)
        if not product:
            return False

        shard = self.get_shard_for_price(product['Price'])
        try:
            with self.connections[shard].cursor() as cur:
                cur.execute("DELETE FROM Products WHERE ProductID = %s", (product_id,))
            with self.connections['central'].cursor() as cur_central:
                cur_central.execute(
                    """INSERT INTO InventoryLogs (ProductID, ChangeType, QuantityChanged)
                    VALUES (%s, %s, %s)""",
                    (product_id, 'delete', 0)
                )
            self.connections[shard].commit()
            self.connections['central'].commit()
            return True
        except Exception as e:
            self.connections[shard].rollback()
            self.connections['central'].rollback()
            raise Exception(f"Failed to delete product: {str(e)}")

    def get_shard_counts(self) -> Dict[str, int]:
        """Get the total number of products in each shard."""
        counts = {}
        for shard in ['low_price', 'mid_price', 'high_price']:
            with self.connections[shard].cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM Products")
                counts[shard] = cur.fetchone()[0]
        return counts

    def __del__(self):
        """Close all database connections."""
        for conn in self.connections.values():
            conn.close()

def main():
    inventory = InventorySystem()
    try:
        # Add a category
        inventory.add_category(3, "Clothing")
        print("Added category: Clothing (ID: 3)")

        # Add a supplier
        inventory.add_supplier(3, "ClothDist", "clothdist@example.com")
        print("Added supplier: ClothDist (ID: 3)")

        # Add a product
        product_id = inventory.add_product(
            name="T-Shirt", description="Cotton T-shirt", price=25.00,
            stock_quantity=50, category_id=3, supplier_id=3
        )
        print(f"Added product with ID: {product_id}")

        # Retrieve by ID
        product = inventory.get_product_by_id(product_id)
        print(f"Product: {product}")

        # Retrieve by price range
        products = inventory.get_products_by_price_range(0, 50)
        print(f"Products in price range: {products}")

        # List all products
        all_products = inventory.list_all_products()
        print(f"All products: {all_products}")

        # Update price (same shard)
        inventory.update_product_price(product_id, 30.00)
        print("Updated price within same shard")

        # Update price (different shard)
        inventory.update_product_price(product_id, 600.00)
        print("Updated price with shard migration")

        # Update stock
        inventory.update_stock_quantity(product_id, -5)
        print("Updated stock quantity")

        # Get shard counts
        counts = inventory.get_shard_counts()
        print(f"Shard counts: {counts}")

        # Delete product
        inventory.delete_product(product_id)
        print("Deleted product")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()