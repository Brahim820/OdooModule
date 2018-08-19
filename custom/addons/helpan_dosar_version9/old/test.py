from openerp import api,fields, models

class ResCompanyPhoneModification(models.Model):
    _inherit='res.company'

@api.multi
def updatePhoneNumber(self,new_number):
    self.ensure_one()
    company_user = self.sudo() # new Boss - nou mediu - superuser Administrator
    # daca e gol - Administrator , altfel se duce la alt utilizator
    # toate comenzile urmatoare vor fi date ca admin
    company_user.phone = new_number


#modified context !
#cum sa citim nivelul de stoc pentru produs dintr-o locatie
# model stock si produs
class product_product(models.Model):
    _name='product.product'
    name=fields.Char('Name',required=True)
    qty_available=fields.Float('Qty at Hand',compute='_product_available')

    def _product_available(self):
        """daca avem contextul legat de o cheie  location legata la baza de date, calculam stocul doar
        pentru locatia respectiva. Altfel aratam tot stocul"""
        pass # citeste sursa adevarata din addons/stock/product.py - adica efectiv du-ten acolo
    
class ProductProduct(models.Model):
    _inherit='product.product'
    @api.multi
    def stock_in_location(self,location):
        product_in_loc=self.with_context(
            location=location.id,
            active_test=False       # daca avem produse sterse - le afiseaza si pe astea !
        )
        all_product=product_in_loc.search([])
        stock_levels=[]
        for product in all_product:
            if product.qty_available:
                stock_levels.append(product.name,product.qty_available)
        return stock_levels
new_context = self.env.context.copy()
new_context.update({'location':location.id,'active_test':False})  # avem context nou cu dictionat !@!!

#tuples vs dictionarys