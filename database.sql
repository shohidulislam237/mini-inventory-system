-- Central Database Setup
CREATE DATABASE IF NOT EXISTS inventory_central;
USE inventory_central;

CREATE TABLE IF NOT EXISTS InventoryLogs (
    LogID INT AUTO_INCREMENT PRIMARY KEY,
    ProductID CHAR(36) NOT NULL,
    ChangeType VARCHAR(50) NOT NULL,
    QuantityChanged INT NOT NULL,
    LogTimestamp DATETIME DEFAULT NOW()
);

-- Low Price Shard
CREATE DATABASE IF NOT EXISTS inventory_low;
USE inventory_low;

CREATE TABLE IF NOT EXISTS Categories (
    CategoryID INT PRIMARY KEY,
    CategoryName VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS Suppliers (
    SupplierID INT PRIMARY KEY,
    SupplierName VARCHAR(100) NOT NULL,
    ContactInfo VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS Products (
    ProductID CHAR(36) PRIMARY KEY,
    ProductName VARCHAR(100) NOT NULL,
    Description TEXT,
    Price DECIMAL(10,2) NOT NULL,
    CONSTRAINT CHK_Price_Low CHECK (Price < 50.00),
    StockQuantity INT NOT NULL DEFAULT 0,
    CONSTRAINT CHK_Stock_Low CHECK (StockQuantity >= 0),
    CategoryID INT,
    SupplierID INT,
    DateAdded DATETIME DEFAULT NOW(),
    LastUpdated DATETIME DEFAULT NOW(),
    FOREIGN KEY (CategoryID) REFERENCES Categories(CategoryID),
    FOREIGN KEY (SupplierID) REFERENCES Suppliers(SupplierID)
);

-- Mid Price Shard
CREATE DATABASE IF NOT EXISTS inventory_mid;
USE inventory_mid;

CREATE TABLE IF NOT EXISTS Categories (
    CategoryID INT PRIMARY KEY,
    CategoryName VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS Suppliers (
    SupplierID INT PRIMARY KEY,
    SupplierName VARCHAR(100) NOT NULL,
    ContactInfo VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS Products (
    ProductID CHAR(36) PRIMARY KEY,
    ProductName VARCHAR(100) NOT NULL,
    Description TEXT,
    Price DECIMAL(10,2) NOT NULL,
    CONSTRAINT CHK_Price_Mid CHECK (Price >= 50.00 AND Price < 500.00),
    StockQuantity INT NOT NULL DEFAULT 0,
    CONSTRAINT CHK_Stock_Mid CHECK (StockQuantity >= 0),
    CategoryID INT,
    SupplierID INT,
    DateAdded DATETIME DEFAULT NOW(),
    LastUpdated DATETIME DEFAULT NOW(),
    FOREIGN KEY (CategoryID) REFERENCES Categories(CategoryID),
    FOREIGN KEY (SupplierID) REFERENCES Suppliers(SupplierID)
);

-- High Price Shard
CREATE DATABASE IF NOT EXISTS inventory_high;
USE inventory_high;

CREATE TABLE IF NOT EXISTS Categories (
    CategoryID INT PRIMARY KEY,
    CategoryName VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS Suppliers (
    SupplierID INT PRIMARY KEY,
    SupplierName VARCHAR(100) NOT NULL,
    ContactInfo VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS Products (
    ProductID CHAR(36) PRIMARY KEY,
    ProductName VARCHAR(100) NOT NULL,
    Description TEXT,
    Price DECIMAL(10,2) NOT NULL,
    CONSTRAINT CHK_Price_High CHECK (Price >= 500.00),
    StockQuantity INT NOT NULL DEFAULT 0,
    CONSTRAINT CHK_Stock_High CHECK (StockQuantity >= 0),
    CategoryID INT,
    SupplierID INT,
    DateAdded DATETIME DEFAULT NOW(),
    LastUpdated DATETIME DEFAULT NOW(),
    FOREIGN KEY (CategoryID) REFERENCES Categories(CategoryID),
    FOREIGN KEY (SupplierID) REFERENCES Suppliers(SupplierID)
);

