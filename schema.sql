-- 1. Tabel Dimensi Waktu
CREATE TABLE Dim_Time (
    Time_ID SERIAL PRIMARY KEY,
    Date DATE UNIQUE,
    Day INT,
    Month INT,
    Year INT,
    Quarter INT
);

-- 2. Tabel Dimensi Layanan
CREATE TABLE Dim_Service (
    Service_ID SERIAL PRIMARY KEY,
    Service_Type VARCHAR(50),
    Service_Name VARCHAR(100),
    SLA_Days INT
);

-- 3. Tabel Dimensi Tujuan/Destinasi
CREATE TABLE Dim_Destination (
    Destination_ID SERIAL PRIMARY KEY,
    Receiver_Address TEXT,
    District VARCHAR(100),
    City VARCHAR(100),
    Province VARCHAR(100),
    ZIP_Code VARCHAR(20)
);

-- 4. Tabel Dimensi Status Pengiriman
CREATE TABLE Dim_Status (
    Status_ID SERIAL PRIMARY KEY,
    Status_Name VARCHAR(50)
);

-- 5. Tabel Dimensi Alasan Keterlambatan
CREATE TABLE Dim_Reason (
    Reason_ID SERIAL PRIMARY KEY,
    Reason_Category VARCHAR(100),
    Description TEXT
);

-- 6. Tabel Dimensi Cabang/Branch
CREATE TABLE Dim_Branch (
    Branch_ID SERIAL PRIMARY KEY,
    Branch_Code VARCHAR(20),
    Branch_Name VARCHAR(100),
    City VARCHAR(100),
    Region_Province VARCHAR(100)
);

-- 7. Tabel Dimensi Barang (Item)
CREATE TABLE Dim_Item (
    Item_ID SERIAL PRIMARY KEY,
    Item_Name VARCHAR(200),
    Item_Category VARCHAR(100),
    Weight_Kg DECIMAL(10, 2),
    Fragile_Status BOOLEAN
);

-- 8. Tabel Dimensi Rute Pengiriman
CREATE TABLE Dim_Route (
    Route_ID SERIAL PRIMARY KEY,
    Origin_City VARCHAR(100),
    Transit_Point VARCHAR(100),
    Destination_City_Code VARCHAR(20)
);

-- 9. Tabel Dimensi Pelanggan (Customer)
CREATE TABLE Dim_Customer (
    Customer_ID SERIAL PRIMARY KEY,
    Customer_Name VARCHAR(200),
    Customer_Type VARCHAR(50),
    Phone_Number VARCHAR(50)
);

-- 10. Tabel Fakta Pengiriman (Fact_Shipping)
-- Ini adalah tabel pusat yang menghubungkan semua dimensi
CREATE TABLE Fact_Shipping (
    Shipping_Fact_ID SERIAL PRIMARY KEY,
    Time_ID INT REFERENCES Dim_Time(Time_ID),
    Branch_ID INT REFERENCES Dim_Branch(Branch_ID),
    Service_ID INT REFERENCES Dim_Service(Service_ID),
    Destination_ID INT REFERENCES Dim_Destination(Destination_ID),
    Item_ID INT REFERENCES Dim_Item(Item_ID),
    Route_ID INT REFERENCES Dim_Route(Route_ID),
    Customer_ID INT REFERENCES Dim_Customer(Customer_ID),
    Status_ID INT REFERENCES Dim_Status(Status_ID),
    Reason_ID INT REFERENCES Dim_Reason(Reason_ID),
    Nomor_Resi VARCHAR(50),
    Shipping_Duration INT,
    Shipping_Cost DECIMAL(15, 2),
    Is_Late INT
);