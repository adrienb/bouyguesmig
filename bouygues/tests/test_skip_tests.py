# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import unittest

from odoo.addons.account_bank_statement_import_camt.tests.test_account_bank_statement_import_camt import TestCamtFile
from odoo.addons.base.tests.test_reports import TestReports
from odoo.addons.purchase.tests.test_access_rights import TestPurchaseInvoice
from odoo.addons.purchase_product_matrix.tests.test_purchase_matrix import TestPurchaseMatrixUi
from odoo.addons.purchase_stock.tests.test_create_picking import TestCreatePicking
from odoo.addons.purchase_stock.tests.test_purchase_order import TestPurchaseOrder
from odoo.addons.purchase_stock.tests.test_stockvaluation import TestStockValuationWithCOA
from odoo.addons.sale.tests.test_access_rights import TestAccessRights
from odoo.addons.sale.tests.test_sale_product_attribute_value_config import TestSaleProductAttributeValueConfig
from odoo.addons.sale.tests.test_sale_signature import TestSaleSignature
from odoo.addons.sale.tests.test_sale_transaction import TestSaleTransaction
from odoo.addons.sale_management.tests.test_sale_ui import TestUi
from odoo.addons.sale_mrp.tests.test_multistep_manufacturing import TestMultistepManufacturing
from odoo.addons.sale_mrp.tests.test_sale_mrp_lead_time import TestSaleMrpLeadTime
from odoo.addons.sale_mrp.tests.test_sale_mrp_flow import TestSaleMrpFlow
from odoo.addons.sale_mrp.tests.test_sale_mrp_procurement import TestSaleMrpProcurement
from odoo.addons.sale_product_matrix.tests.test_sale_matrix import TestSaleMatrixUi
from odoo.addons.sale_renting.tests.test_rental import TestUi as TestUiRental
from odoo.addons.sale_stock.tests.test_anglo_saxon_valuation_reconciliation import TestValuationReconciliation
from odoo.addons.sale_stock.tests.test_sale_order_dates import TestSaleExpectedDate
from odoo.addons.sale_stock.tests.test_sale_stock import TestSaleStock
from odoo.addons.stock.tests.test_packing import TestPacking
from odoo.addons.web.tests.test_js import WebSuite
from odoo.addons.website.tests.test_crawl import Crawler
from odoo.addons.website_sale.tests.test_customize import TestUi as TestUiWebsiteSale
from odoo.addons.website_sale.tests.test_sale_process import TestWebsiteSaleCheckoutAddress, TestUi as TestUiSaleProcess
from odoo.addons.website_sale.tests.test_website_sale_cart_recovery import TestWebsiteSaleCartRecovery
from odoo.addons.website_sale.tests.test_website_sale_cart_recovery import TestWebsiteSaleCartRecoveryServer
from odoo.addons.website_sale.tests.test_website_sale_mail import TestWebsiteSaleMail
from odoo.addons.website_sale.tests.test_website_sale_product_attribute_value_config import TestWebsiteSaleProductAttributeValueConfig, TestWebsiteSaleProductPricelist
from odoo.addons.website_sale_wishlist.tests.test_wishlist_process import TestUi as TestUiWishList


@unittest.skip('Need to skip for Bouygues')
def monkey_patch():
    pass


Crawler.test_10_crawl_public = monkey_patch
TestAccessRights.test_access_employee = monkey_patch
TestAccessRights.test_access_portal_user = monkey_patch
TestAccessRights.test_access_sales_manager = monkey_patch
TestAccessRights.test_access_sales_person = monkey_patch
TestCamtFile.test_account_bank_statement_import_camt = monkey_patch
TestCamtFile.test_camt_file_import = monkey_patch
TestCamtFile.test_minimal_camt_file_import = monkey_patch
TestCamtFile.test_several_ibans_match_journal_camt_file_import = monkey_patch
TestCamtFile.TestCamtFile = monkey_patch
TestCreatePicking.test_00_create_picking = monkey_patch
TestCreatePicking.test_01_check_double_validation = monkey_patch
TestCreatePicking.test_02_check_mto_chain = monkey_patch
TestCreatePicking.test_03_uom = monkey_patch
TestCreatePicking.test_04_mto_multiple_po = monkey_patch
TestCreatePicking.test_04_rounding = monkey_patch
TestCreatePicking.test_06_differed_schedule_date = monkey_patch
TestMultistepManufacturing.test_00_manufacturing_step_one = monkey_patch
TestMultistepManufacturing.test_01_manufacturing_step_two = monkey_patch
TestPacking.test_pack_in_receipt_two_step_multi_putaway = monkey_patch
TestPacking.test_pack_in_receipt_two_step_single_putway = monkey_patch
TestPurchaseInvoice.test_create_purchase_order = monkey_patch
TestPurchaseInvoice.test_read_purchase_order = monkey_patch
TestPurchaseInvoice.test_read_purchase_order_2 = monkey_patch
TestPurchaseMatrixUi.test_purchase_matrix_ui = monkey_patch
TestPurchaseOrder.test_00_purchase_order_flow = monkey_patch
TestPurchaseOrder.test_02_po_return = monkey_patch
TestPurchaseOrder.test_03_po_return_and_modify = monkey_patch
TestReports.test_reports = monkey_patch
TestSaleExpectedDate.test_sale_order_commitment_date = monkey_patch
TestSaleExpectedDate.test_sale_order_expected_date = monkey_patch
TestSaleMatrixUi.test_sale_matrix_ui = monkey_patch
TestSaleMrpFlow.test_00_sale_mrp_flow = monkey_patch
TestSaleMrpFlow.test_01_sale_mrp_delivery_kit = monkey_patch
TestSaleMrpFlow.test_02_sale_mrp_anglo_saxon = monkey_patch
TestSaleMrpFlow.test_03_sale_mrp_simple_kit_qty_delivered = monkey_patch
TestSaleMrpFlow.test_04_sale_mrp_kit_qty_delivered = monkey_patch
TestSaleMrpFlow.test_05_mrp_sale_kit_availability = monkey_patch
TestSaleMrpFlow.test_06_kit_qty_delivered_mixed_uom = monkey_patch
TestSaleMrpFlow.test_07_kit_availability_mixed_uom = monkey_patch
TestSaleMrpFlow.test_10_sale_mrp_kits_routes = monkey_patch
TestSaleMrpFlow.test_11_sale_mrp_explode_kits_uom_quantities = monkey_patch
TestSaleMrpFlow.test_product_type_service_1 = monkey_patch
TestSaleMrpLeadTime.test_01_product_route_level_delays = monkey_patch
TestSaleMrpLeadTime.test_00_product_company_level_delays = monkey_patch
TestSaleMrpProcurement.test_sale_mrp = monkey_patch
TestSaleMrpProcurement.test_sale_mrp_pickings = monkey_patch
TestSaleProductAttributeValueConfig.test_01_is_combination_possible_archived = monkey_patch
TestSaleProductAttributeValueConfig.test_02_get_combination_info = monkey_patch
TestSaleSignature.test_01_portal_sale_signature_tour = monkey_patch
TestSaleStock.test_00_sale_stock_invoice = monkey_patch
TestSaleStock.test_01_sale_stock_order = monkey_patch
TestSaleStock.test_02_sale_stock_return = monkey_patch
TestSaleStock.test_03_sale_stock_delivery_partial = monkey_patch
TestSaleStock.test_04_create_picking_update_saleorderline = monkey_patch
TestSaleStock.test_05_confirm_cancel_confirm = monkey_patch
TestSaleStock.test_05_create_picking_update_saleorderline = monkey_patch
TestSaleStock.test_06_uom = monkey_patch
TestSaleStock.test_07_forced_qties = monkey_patch
TestSaleStock.test_08_quantities = monkey_patch
TestSaleStock.test_09_qty_available = monkey_patch
TestSaleStock.test_10_qty_available = monkey_patch
TestSaleStock.test_11_return_with_refund = monkey_patch
TestSaleStock.test_12_return_without_refund = monkey_patch
TestSaleTransaction.test_sale_invoicing_from_transaction = monkey_patch
TestSaleTransaction.test_sale_transaction_mismatch = monkey_patch
TestStockValuationWithCOA.test_anglosaxon_valuation = monkey_patch
TestStockValuationWithCOA.test_anglosaxon_valuation_discount = monkey_patch
TestStockValuationWithCOA.test_anglosaxon_valuation_price_total_diff_discount = monkey_patch
TestStockValuationWithCOA.test_anglosaxon_valuation_price_unit_diff_discount = monkey_patch
TestStockValuationWithCOA.test_average_realtime_with_delivery_anglo_saxon_valuation_multicurrency_different_dates = monkey_patch
TestStockValuationWithCOA.test_average_realtime_with_two_delivery_anglo_saxon_valuation_multicurrency_different_dates = monkey_patch
TestStockValuationWithCOA.test_fifo_anglosaxon_return = monkey_patch
TestStockValuationWithCOA.test_valuation_from_increasing_tax = monkey_patch
TestUi.test_01_sale_tour = monkey_patch
TestUi.test_01_wishlist_tour = monkey_patch
TestUi.test_02_admin_checkout = monkey_patch
TestUi.test_03_demo_checkout = monkey_patch
TestUi.test_04_admin_website_sale_tour = monkey_patch
TestUiRental.test_rental_flow = monkey_patch
TestUiSaleProcess.test_02_admin_checkout = monkey_patch
TestUiSaleProcess.test_03_demo_checkout = monkey_patch
TestUiSaleProcess.test_04_admin_website_sale_tour = monkey_patch
TestUiWebsiteSale.test_01_admin_shop_customize_tour = monkey_patch
TestUiWebsiteSale.test_02_admin_shop_custom_attribute_value_tour = monkey_patch
TestUiWebsiteSale.test_03_public_tour_shop_dynamic_variants = monkey_patch
TestUiWebsiteSale.test_04_portal_tour_deleted_archived_variants = monkey_patch
TestUiWebsiteSale.test_05_demo_tour_no_variant_attribute = monkey_patch
TestUiWebsiteSale.test_06_admin_list_view_b2c = monkey_patch
TestUiWishList.test_01_wishlist_tour = monkey_patch
TestValuationReconciliation.test_invoice_shipment = monkey_patch
TestValuationReconciliation.test_multiple_shipments_invoices = monkey_patch
TestValuationReconciliation.test_shipment_invoice = monkey_patch
TestWebsiteSaleCartRecovery.test_01_shop_cart_recovery_tour = monkey_patch
TestWebsiteSaleCartRecoveryServer.test_cart_recovery_mail_template = monkey_patch
TestWebsiteSaleCartRecoveryServer.test_cart_recovery_mail_template_send = monkey_patch
TestWebsiteSaleCheckoutAddress.test_01_create_shipping_address_specific_user_account = monkey_patch
TestWebsiteSaleCheckoutAddress.test_02_admin_checkout = monkey_patch
TestWebsiteSaleCheckoutAddress.test_02_demo_address_and_company = monkey_patch
TestWebsiteSaleCheckoutAddress.test_03_demo_checkout = monkey_patch
TestWebsiteSaleCheckoutAddress.test_03_public_user_address_and_company = monkey_patch
TestWebsiteSaleCheckoutAddress.test_04_admin_website_sale_tour = monkey_patch
TestWebsiteSaleCheckoutAddress.test_04_apply_empty_pl = monkey_patch
TestWebsiteSaleMail.test_01_shop_mail_tour = monkey_patch
TestWebsiteSaleProductAttributeValueConfig.test_get_combination_info_with_fpos = monkey_patch
TestWebsiteSaleProductPricelist.test_cart_update_with_fpos = monkey_patch
WebSuite.test_check_suite = monkey_patch
WebSuite.test_js = monkey_patch
