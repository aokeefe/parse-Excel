import xlrd  # read from and excel (http://pypi.python.org/pypi/xlrd)
import xlwt  # write to excel
import pylib.osscripts as oss # custom library
# import pylib.aoh.aohDBfromDict as stdb # my custom database from dictionary
# import pylib.aoh.aohHTMLUtils as utils # my custom utilities
# import re # regular expression
#
# =================================================================================
# Author: 
#         Amy O'Keefe // amy.okeefe@rochesterregional.org
#         (c) 2015
# Website: 
#         www.amyoh.com 
# Purpose: 
#         Read in InterVol account MS Excel (.xls) files and generate custom formated output Excel files. 
# Note: 
#         Excel import files need to be .xls -- Older version of Excel!
# 
# Code Resources:
# - code BLOG: http://mherman.org/blog/2012/09/30/import-data-from-excel-into-mysql-using-python/
# - See also YouTube video: http://www.python-excel.org/
# - See dictionary xf_dict in file C:/Python26/Lib/Site-Packages/xlwt/Style.py
#
# TODOs:  
# - TODO Add Error / (try / except) checking for valid files, inputs, etc.
# - TODO Write function to compare differences between 2 spreadsheets
# - TODO Handle spreadsheet generated by volunteer sign ins (Google Doc).
# - TODO Generate special reports (e.g., Dr. Pennino wants all donations over $50 for Haiti Orphange)
#
# =================================================================================

# Excel column letters to numbers - used for code readability:
A, B, C, D, E, F, G, H, I, J, K, L, M = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12
N, O, P, Q, R, S, T, U, V, W, X, Y, Z = 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25  # (Z=25 (count started at A=0))
AA, AB = 26, 27

# Cell Formats: (See dictionary xf_dict in file C:/Python26/Lib/Site-Packages/xlwt/Style.py)
class CellFormats():
    """ Formats and Formulas for Excel cell values (e.g., heading, totals, money, dates)   
    """
    def __init__(self, dbug=0):
        ezxf = xlwt.easyxf
        self.heading = ezxf('font: bold on; align: wrap no, horiz left') # vert center, horiz center')
        self.total = ezxf('font: bold on; align: wrap no, horiz right; pattern: pattern solid, fore_colour yellow; border: top thin;') 
        self.money = ezxf( num_format_str='$#,##0.00')
        self.money_hl = ezxf('pattern: pattern solid, fore_colour yellow; border: top thin;', num_format_str='$#,##0.00')
        #self.money_it = ezxf('font: italic true; pattern: pattern solid, fore_colour white', num_format_str='$#,##0.00')
        self.date = ezxf('font: italic true; pattern: pattern solid, fore_colour white',  num_format_str='MM-DD-YYYY')
        #self.num = ezxf('', num_format_str='00')
        
    def sum(self, firstrow, lastrow, column):
        """ Return Excel formula SUM (e.g., sum of column D, rows 2-10 == SUM(D2:D10)) 
        """
        return "SUM($%s%d:$%s%d)" % (column, firstrow, column, lastrow) 
    
    def add_copyright(self, ws, row):
        """ Add copy right message to bottom of worksheet. Return next available row number.
        """
        cpyrt = "[amypy:intervol_parse_excel_files_sample.py (c) 2015 amypy/]" 
        ws.write (row+2, 0, cpyrt) 
        return row+3
    
# ------------------------------------------------------------------------------------------------
# Read Crowdrise Excel Workbook Sheet 
#
def read_Crowdrise_sheet(sheet):
    """ Read a Crowdrise generated report file (.xls)   
        Row by row read a sheet from a Crowdrise generated report saved as xls (Older version of Excel!).
        Only a subset of the data pulled is put into a dictionary and returned
    """  
    crDict = {}
    for r in range(1, sheet.nrows):
        refId = sheet.cell(r, C).value   # Assumes all ref id's are unique in the Crowdrise file/report.
        paidas = sheet.cell(r, X).value  # e.g., WePay, Network for Good
        if paidas == "Not Donated Through CrowdRise": # skip these
            continue
        transdate = sheet.cell(r, A).value  # transfer date
        donAmount = sheet.cell(r, E).value  # !!! TODO This can be a negative number if a refund !!!     
        donFee = sheet.cell(r, F).value     # F total fee
        donNetAmt = sheet.cell(r, G).value  # G net donation (donation - fee)
        donFirstName = sheet.cell(r, I).value
        donLastName = sheet.cell(r, J).value
        donEmail = sheet.cell(r, L).value
        donAddr1 = sheet.cell(r, M).value
        donAddr2 = sheet.cell(r, N).value
        donAddr3 = sheet.cell(r, O).value
        donCity = sheet.cell(r, P).value
        donState = sheet.cell(r, Q).value
        donZip = sheet.cell(r, R).value
        donPhone = sheet.cell(r, S).value
        projCampaign = sheet.cell(r, U).value
        # V project owner first name
        ownerFirstName = sheet.cell(r, V).value
        # W project owner last name
        ownerLastName = sheet.cell(r, W).value
        # ...
        # (AB Fundraiser ID (unique to project owner))
        ownerUniqueID =  sheet.cell(r, AB).value 
        # ... 
        # projOwnerEmail = sheet.cell(r,AG).value
        
        crDict[refId] = {'first name':donFirstName, 'last name':donLastName, 'email' :donEmail, 'amount':donAmount ,
                         'fee':donFee, 'net':donNetAmt, 'campaign':projCampaign,
                         'addr1':donAddr1, 'addr2':donAddr2, 'addr3':donAddr3, 'city':donCity, 'state':donState, 'zip':donZip, 'phone':donPhone,
                         'ownerFirstName':ownerFirstName, 'ownerLastName' : ownerLastName,
                         'ownerID': ownerUniqueID, 'paid as': paidas, 'transdate':transdate, 'filetype':"Crowdrise"}
    return crDict

# ------------------------------------------------------------------------------------------------
# Write Crowdrise Excel Workbook Sheet
#
def write_Crowdrise_sheet(indict, newWb, row=0):
    """ Add a new "Crowdrise" sheet to workbook (newWb) using data from dictionary (indict); Start at given row number.
        indict is generated by read_Crowdrise_sheet
        returns next empty row number
    """
    # TODO Handle project owner -- keep track of how much each owner raised under their name, etc.
    ws = newWb.add_sheet('Crowdrise Data Subset')
    cf = CellFormats()
    
    ws.write(row, A, "First Name", cf.heading)
    ws.write(row, B, "Last Name", cf.heading)
    ws.write(row, C, "EMail", cf.heading)
    ws.write(row, D, "Donation", cf.heading)
    ws.write(row, E, "Net", cf.heading)
    ws.write(row, F, "Campaign", cf.heading)
    ws.write(row, G, "Owner Last Name", cf.heading)
    ws.write(row, H, "Date", cf.heading)
    row += 1
    rowstart = row
    
    if len(indict):
        for refid, d in indict.items():  # (refid ignored)
            ws.write (row, A, d['first name'] )
            ws.write (row, B, d['last name'] )
            ws.write (row, C, d['email'])
            ws.write (row, D, d['amount'], cf.money)
            ws.write (row, E, d['net'], cf.money)
            ws.write (row, F, d['campaign'])
            ws.write (row, G, d['ownerLastName'])
            ws.write (row, H, d['transdate'], cf.date)
            
            row += 1
            
    # Add SUM formula to total the amount of money (col D):
    ws.write(row, C, "TOTAL: ", cf.total)
    formula = cf.sum(rowstart, row, "D")
    ws.write(row, D, xlwt.Formula(formula), cf.money_hl)   # Amounts

    # Add SUM formula to total net (col E):
    formula = cf.sum(rowstart, row, "E")
    ws.write(row, E, xlwt.Formula(formula), cf.money_hl)  # Net
              
    return cf.add_copyright(ws, row)    
     
# ------------------------------------------------------------------------------------------------
# Read MailChimp Excel Workbook Sheet
#
def read_MailChimp_sheet(sheet):
    """ Read a MailChimp generated report file (.xls)   
        Row by row read a sheet from a MailChimp generated report saved as xls (Older version of Excel!).
    """   
    # MailChimp collects: First Name, Last Name, and EMail addresses.
      
    mcDict = {}
    
    for r in range(1, sheet.nrows):
        refId = r
        email = sheet.cell(r, A).value     # email address required
        firstname = sheet.cell(r, B).value # (optional)
        lastname = sheet.cell(r, C).value  # (optional)
              
        mcDict[refId] = {'first name':firstname, 'last name':lastname, 'email' :email, 
                         'filetype':"MailChimp" }
    return mcDict   

# ------------------------------------------------------------------------------------------------
# Write MailChimp Workbook Sheet
#
def write_MailChimp_sheet(indict, newWb, row=0):
    """ Add a new "MailChimp" sheet to workbook (newWb) using data from dictionary (indict); Start at given row number.
        indict is generated by read_MailChimp_sheet
        returns next empty row number
    """
    ws = newWb.add_sheet('MailChimp Data') # Add new sheet to workbook, newWb
    cf = CellFormats()
    
    # Write column headers:
    ws.write(row, A, "First Name", cf.heading)
    ws.write(row, B, "Last Name", cf.heading)
    ws.write(row, C, "EMail", cf.heading)
    row += 1
    
    if len(indict):
        #items = [(v, k) for k, v in indict.items()] # flip key,val to val,key ...
        #items.sort() 
        for refid, d in indict.items():  # (refid ignored)
            # Write row of data:
            ws.write (row, A, d['first name']) # (some entries do not have a first and last name)
            ws.write (row, B, d['last name'])
            ws.write (row, C, d['email'])      # all have at least an email address
            row += 1  
            
    return cf.add_copyright(ws, row) 

# ------------------------------------------------------------------------------------------------
# Read ROC the Day Excel Workbook Sheet
#
def read_ROC_sheet(sheet):
    """ Read a ROC the Day generated report file (.xls) 
        Row by row read a sheet from a ROC the Day generated report saved as xls (Older version of Excel!).
        Only a subset of the data pulled is put into a dictionary and return it, "rocDict"
    """  
    # "ROC the Day" (2013) input columns: 
    #  PENDING    campaign    FirstName    LastName    RecognitionName    F:EmailAddress    
    #  DonorAddress    City    State    J:ZipCode    Purchase Type    Agency DBA Name    
    #  Book Number    ANDAR #    Amount To Agency    CoverFees    Fee Amt# Covered By Donor (Included In Total To Acknowledge)    
    #  Total Amt# To Acknowledge To Donor (Gift + Any Fee Covered)    DonationComment    Memory or Honor    Memory Or Honor Name    
    #  MemoryOrHonorComment    DonationDate
  
    rocDict = {}
    for r in range(1, sheet.nrows):
        refId = r
        
        # A-B
        donFirstName = sheet.cell(r, C).value
        donLastName = sheet.cell(r, D).value
        # E
        donEmail = sheet.cell(r, F).value
        donAddr1 = sheet.cell(r, G).value
        donCity = sheet.cell(r, H).value
        donState = sheet.cell(r, I).value
        donZip = sheet.cell(r, J).value
        # K-N
        donAmount = sheet.cell(r, O).value 
        # P
        fee = sheet.cell(r, Q).value    # fee paid by donor
        # R-T
        inhonor = sheet.cell(r, U).value
        projCampaign = "General Donation"
       
        rocDict[refId] = {'first name':donFirstName, 'last name':donLastName, 'email' :donEmail,
                         'amount':donAmount, 'fee':fee, 'campaign':projCampaign,
                         'addr1':donAddr1, 'city':donCity, 'state':donState, 'zip':donZip, 'inhonor':inhonor,
                         'filetype':"ROCtheDay" }
    return rocDict   

# ------------------------------------------------------------------------------------------------
# Write ROC the Day Excel Workbook Sheet
#
def write_ROC_sheet(indict, newWb, row=0):
    """ Add a new "ROC the Day" sheet to workbook (newWb) using data from dictionary (indict); Start at given row number.
        indict is generated by read_ROC_sheet
        returns next empty row number
    """
    ws = newWb.add_sheet('ROC Data Subset')
    cf = CellFormats()
    
    # Write column headers:
    ws.write(row, A, "First Name", cf.heading)
    ws.write(row, B, "Last Name", cf.heading)
    ws.write(row, C, "EMail", cf.heading)
    ws.write(row, D, "Amount", cf.heading)
    ws.write(row, E, "Fee Pd By Donor", cf.heading)
    ws.write(row, F, "In Honor Of", cf.heading)

    row += 1
    rowstart = row
    
    if len(indict):
        for refid, d in indict.items():  # (refid ignored)
            # Write row of data:
            ws.write (row, A, d['first name'])
            ws.write (row, B, d['last name'])
            ws.write (row, C, d['email'])
            ws.write (row, D, d['amount'], cf.money)
            ws.write (row, E, d['fee'], cf.money)
            ws.write (row, F, d['inhonor'])
            row += 1  
          
    # Add SUM formula to total amount of money (col D):
    ws.write(row, C, "TOTAL: ", cf.total)
    formula = cf.sum(rowstart, row, "D")
    ws.write(row, D, xlwt.Formula(formula), cf.money_hl)  # 

    # Add SUM formula to total fees (col E):
    formula = cf.sum(rowstart, row, "E")
    ws.write(row, E, xlwt.Formula(formula), cf.money_hl)   # fee
    
    return cf.add_copyright(ws, row) 
     
# ------------------------------------------------------------------------------------------------
# Read Little Green Light (LGL) Excel Workbook Sheet
#
def read_LGL_sheet(sheet):
    """ Read a LGL generated report file (.xls) 
        Row by row read a sheet from a Little Green Light (LGL) generated report saved as xls (Older version of Excel!).
        Only a subset of the data pulled is put into a dictionary and return it, "lglDict"
    """  
    # 
    lglDict = {}
    for r in range(1, sheet.nrows):
        refId = r
        
        # A-D
        campaign = sheet.cell(r, E).value
        fund = sheet.cell(r, F).value
        # G
        donFirstName = sheet.cell(r, H).value
        # I
        donLastName = sheet.cell(r, J).value
        organization = sheet.cell(r, K).value
        # L          
        donAddr1 = sheet.cell(r, M).value
        donCity = sheet.cell(r, N).value
        donState = sheet.cell(r, O).value
        donZip = sheet.cell(r, P).value   
        # Q-R           
        donEmail = sheet.cell(r, S).value
        # T phone
        donAmount = sheet.cell(r, U).value
        # V deposit date      
        payType = sheet.cell(r, W).value
        payRef = sheet.cell(r, X).value
        
        
        lglDict[refId] = {'first name':donFirstName, 'last name':donLastName, 'organization':organization, 'email' :donEmail, 'amount':donAmount , 
                         'addr1':donAddr1, 'city':donCity, 'state':donState, 'zip':donZip, 'fund':fund, 'campaign':campaign,
                         'paytype':payType, 'payref':payRef, 'filetype':"LGL" }

    return lglDict   

# ------------------------------------------------------------------------------------------------
# Write LGL Excel Workbook Sheet
#
def write_LGL_sheet(indict, newWb, row=0):
    """ Add a new LGL sheet to workbook (newWb) using data from dictionary (indict); Start at given row number.
        indict is generated by read_LGL_sheet
        returns next empty row number
    """
    ws = newWb.add_sheet('LGL Subset')
    ws.col(0).width = 3333 # 3333 = 1" (one inch) TODO set col widths (how to auto fit to text??)
    cf = CellFormats()
    
    # Write column headers:
    ws.write(row, A, "First Name", cf.heading)
    ws.write(row, B, "Last Name", cf.heading)
    ws.write(row, C, 'Organization', cf.heading)
    ws.write(row, D, "Amount", cf.heading)
    ws.write(row, E, "Campaign", cf.heading)
    ws.write(row, F, 'Fund', cf.heading)
    ws.write(row, G, "EMail", cf.heading)
    ws.write(row, H, '[Data From]', cf.heading)
    ws.write(row, I, "Address", cf.heading)
    ws.write(row, J, "City", cf.heading)
    ws.write(row, K, "State", cf.heading)
    ws.write(row, L, "Zip", cf.heading)
    ws.write(row, M, 'Payment Type', cf.heading)
    ws.write(row, N, 'Payment Reference', cf.heading)
    
    row += 1
    rowstart = row
    
    if len(indict):
        for refid, d in indict.items():  # (refid ignored)
            filetype = d['filetype'] # Type of input file used 
            # TODO if filetype not 'LGL' return Err
            ws.write (row, A, d['first name'])
            ws.write (row, B, d['last name'])
            ws.write (row, C, d['organization'])                                  
            ws.write (row, D, d['amount'] , cf.money)  
            ws.write (row, E, d['campaign']  )
            ws.write (row, F, d['fund'] )  
            ws.write (row, G, d['email'])
            ws.write (row, H, filetype) # 'LGL'
            ws.write (row, I, d['addr1'])
            ws.write (row, J, d['city'])
            ws.write (row, K, d['state'])
            ws.write (row, L, d['zip'])
            ws.write (row, M, d['paytype'])
            ws.write (row, N, d['payref'] ) 
                         
            row += 1  
            
    # Add SUM formula to total amount of money (col D):
    ws.write(row, C, "TOTAL: ", cf.total)
    formula = cf.sum(rowstart, row, "D")
    ws.write(row, D, xlwt.Formula(formula), cf.money_hl)   # Amount
    
    return cf.add_copyright(ws, row)  
 
# =========================== OTV AUCTION ========================================================
# ------------------------------------------------------------------------------------------------
# Read "Off the Vine" event auction items workbook sheet
#
def read_OTV_Auction(sheet):
    """ Read in OTV Auction Items file (.xls) 
        Return dictionary of date: auctionData
    """  

    auctionData = {}
    for r in range(1, sheet.nrows):
        refId = r
        
        category = sheet.cell(r, A).value
        title = sheet.cell(r, B).value
        value = sheet.cell(r, C).value
        desc = sheet.cell(r, D).value    
        
        auctionData[refId] = {'category':category, 'title':title, 'value':value, 'desc':desc}
    return auctionData   

# ------------------------------------------------------------------------------------------------
# Write "Off the Vine" auction items SQL file
# SQL file used to load MySQL Database for dynamically generated website pages for auction items.
#
def write_SQL_OTV_Auction(indict, sqlfilename, row=0):  
    """ Write OTV auction itme SQL file. Use to load MySQL Database for OTV website.
       indict is generated by read_OTV_Auction
    """

    header = '''-- phpMyAdmin SQL Dump
-- version 2.8.0.1
-- http://www.phpmyadmin.net
-- 
-- amyoh.com converted Excel data to this file (see InterVol_Parse_Excel_Files.py) (c) 2014
--
-- Host: custsql-nf08.eigbox.net
-- Generation Time: May 16, 2014 at 11:05 AM
-- Server version: 5.5.32
-- PHP Version: 4.4.9
-- 
-- Database: `intervolauction`
-- 

-- --------------------------------------------------------

-- 
-- Table structure for table `artwork`
-- 

DROP TABLE IF EXISTS `artwork`;
CREATE TABLE `artwork` (
  `artworkid` int(11) NOT NULL AUTO_INCREMENT COMMENT 'primary key id',
  `title` text NOT NULL,
  `desc` text,
  `startprice` float DEFAULT NULL,
  `imagename` text COMMENT 'filename under images/ dir',
  `bidid` int(11) DEFAULT NULL COMMENT 'id of highest bid (see bids table)',
  `artcategory` text COMMENT 'what category does the art go in (painting, sculpture)',
  `groupname` varchar(50) DEFAULT 'Misc',
  `valueprice` float DEFAULT NULL COMMENT 'what is the piece actually worth?',
  `bidamount` float DEFAULT NULL COMMENT 'current high bid',
  `buyitnow` float DEFAULT NULL COMMENT 'buy it now price',
  `updatedate` text COMMENT 'the last time the highbid was updated',
  `largeimage` text COMMENT 'name of large image file (not cropped)',
  `infofilename` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`artworkid`)
) ENGINE=MyISAM AUTO_INCREMENT=1802 DEFAULT CHARSET=latin1 AUTO_INCREMENT=1802 ;

-- 
-- Dumping data for table `artwork`
-- 

'''
    if oss.exists(sqlfilename):
        oss.mv(sqlfilename, sqlfilename+".BAK.txt")
    #sqlfile = file(sqlfilename, 'w')
    sqlfile = open(sqlfilename, 'w') # open() does an open and ensures a close even if exception
    
    sqlfile.write(header)

    key = 200 
    if len(indict):
        for refid, d in indict.items():  # (refid ignored)
            key += 1            
            title =  d['title']            
            desc = d['desc']
            cat = d['category']
            value= d['value']
            if value < 1:
                value = "NULL"
            sqlstmt  = '''INSERT INTO `artwork` VALUES (%s, '%s', '%s', NULL, 'nopic.png', NULL, '%s', NULL, NULL, NULL, NULL, NULL, 'nopic.png', NULL);
            ''' % ( key, title, desc, cat) #, value )
            sqlfile.write(sqlstmt)
 
    sqlfile.close()
    return    
      

# ================================================================================================
# ------------------------------------------------------------------------------------------------
# main
#

def main():
    outDir = "input_output_files" # directory for input and output files
    
    # Input files: Excel (.xls) files exported from various accounts:
    inExcelCrowd = outDir + "\inCrowdrise.xls"     # InterVol Crowdrise crowd-funding data exported from Crowdrise account
    inExcelLGL = outDir + "\inLGL20140210.xls"     # Little Green Light (LGL) donor mgmt data exported from LGL account
    inExcelROC = outDir + "\inROCtheDay.xls"       # United Way "ROC the Day" data exported from UW account
    inExcelMailChimp = outDir + "\inMailChimp.xls" # MailChimp (bulk emailer) data exported from account
    inExcelOTV = outDir + "\OTVAcutionExcel.xls"   # InterVol "Off the Vine" event action items > Special use to generate an SQL file, not an Excel file.
    #inWooOrders = outDir + "\orders-INPUT-orig.xls"    # WooCommerce (WordPress) online intervolshop.org orders
    #inExcelQuickBooksReport = outDir + "\QBReport.xls" # custom QuickBooks reports
       
    # Output files generated: Excel (.xls) files:
    outExcelCrowd = outDir + "\outCrowd_File.xls"  # out Crowdrise
    outExcelLGL = outDir + "\outLGL_File.xls"      # out LGL
    outExcelROC = outDir + "\outROC_File.xls"      # out ROC the Day
    outExcelMailChimp = outDir + "\outMailChimp_File.xls"    # out MailChimp
    
    # Special output for OTV >> SQL file instead of an Excel file:
    outSQLtxt = outDir + "\OTVAuctionExcelToSQL.txt"  # text file version of .sql file (to easily do a quick read with Notepad)
    sqlfilename = outSQLtxt+".sql" # SQL file to be inported into MySQL database for OTV Auction Items ( for dynamic generation of auction web pages)
 
    
    # *** README: *********************************************************
    # *** README: *********************************************************
    # Steps to add new input Excel files to parse into a customized format:
    # -- Input and output Excel files need to be of the older format ".xls"
    # -- At this time, only the first sheet, 0, of input Excel file is read in.
    #
    # For each new Excel (.xls) input file: 
    #    1. Add the in and out filename variables above. For example, inExcelCrowd and outExcelCrowd.
    #    2. Write the 2 functions:
    #        a. first: to read input Excel (.xls) file: 'readfnc'. For example, read_Crowdrise_sheet()
    #        b. second: to write out new Excel (.xls) file: 'writefnc'. For example, write_Crowdrise_sheet()
    #    3. Then add the new file info to the following python dictionary, 'wbooks'. Easiest to copy one of the key-value pairs and edit it.
    #
    wbooks = { 'Crowdrise':{'infilename': inExcelCrowd, 'outfilename':outExcelCrowd, 'book':0, 'sheet':0, 'newbook':0, 'readfnc': read_Crowdrise_sheet, 'writefnc': write_Crowdrise_sheet}
              ,'LGL': {'infilename': inExcelLGL, 'outfilename':outExcelLGL, 'book':0, 'sheet':0, 'newbook':0, 'readfnc': read_LGL_sheet, 'writefnc': write_LGL_sheet} 
              , 'ROC': {'infilename': inExcelROC, 'outfilename':outExcelROC, 'book':0, 'sheet':0, 'newbook':0, 'readfnc': read_ROC_sheet, 'writefnc': write_ROC_sheet}
              ,'MailChimp': {'infilename': inExcelMailChimp, 'outfilename':outExcelMailChimp, 'book':0, 'sheet':0, 'newbook':0, 'readfnc': read_MailChimp_sheet, 'writefnc': write_MailChimp_sheet}
              , }

    print "Program Start ..."   
                 
    if 1: # Create custom Excel files:
        # For each Excel (.xls) input file in "wbooks", generate a custom Excel output file:   
        for f in wbooks:
            fn = wbooks[f]['infilename']                           # Input filename
            print "Working on ( " + f + " ) Filename: " + fn       # 
            try:
                wbooks[f]['book'] = xlrd.open_workbook(fn)         # Open the input Excel workbook-file.
            except:
                print "*** ERROR: Unable to open file: ", fn, "\n" # ERR unable to open input file
                break
            wbooks[f]['sheet'] = wbooks[f]['book'].sheet_by_index(0)  # Get the first sheet of the input workbook-file. *** ASSUME ONLY LOOKING AT FIRST SHEET
            wDict = wbooks[f]['readfnc'](wbooks[f]['sheet'])          # Read the data and save in the wDict dictionary.
            wbooks[f]['newbook'] = xlwt.Workbook()                    # Initialize a new workbook.
            wbooks[f]['writefnc'](wDict, wbooks[f]['newbook'], 0)     # Write out the new custom sheet using data in wDict.
            try: 
                wbooks[f]['newbook'].save(wbooks[f]['outfilename'])   # Save to new output filename
            except:
                print "*** ERROR: Unable to write file: ", wbooks[f]['outfilename'], " - File may be open.\n" # ERR unable to write new file
                break
            print "___ Done. See new workbook / Excel filename: ", wbooks[f]['outfilename'], "\n" 
            
    # ------------------------------------------------------------------------------------------------
    if 1: # Create SQL file:
            # Special > Output is .sql file instead of another Excel file:
            # InterVol "Off the Vine" Auction Items file in Google Docs > Excel to SQL statements to import int PHPAdmin MySQL DB
            wbook = xlrd.open_workbook(inExcelOTV)   # Open the input Excel workbook-file.
            sheet = wbook.sheet_by_index(0)          # Only first sheet, 0, is looked at
            otvDict = read_OTV_Auction(sheet)          # Read in data from Excel file and save in the otvDict dictionary
            write_SQL_OTV_Auction(otvDict, outSQLtxt)  # Write SQL stmts to output text file (.txt)
            oss.cp(outSQLtxt, sqlfilename)           # Copy output text file to .sql file (for import into MySQL DB)
            print "Done see out file: ", outSQLtxt, " and file: ", sqlfilename   
        
    print "... Program End."
        
        
if __name__ == "__main__":
    main()  # executed as a program (vs included as a library)
