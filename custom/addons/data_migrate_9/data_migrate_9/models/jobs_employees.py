# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# This file is created by gordan.cuic@gmail.com

from openerp import api, fields, models, _, osv
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class DataMigrateOrder(models.Model):
    _inherit = "data.migrate.order"

    @api.model
    def EmployeesPre(self, cr2):
        # hr_department -------------------------------------------------------
        department_obj = self.env['hr.department']
        cr2.execute("""
        select
            d.name -- 0
            ,d.color -- 1
            ,d.message_last_post -- 2
            ,d.company_id -- 3
            ,d.note -- 4
            ,d.parent_id -- 5
            ,d.manager_id -- 6
            ,d.id -- 7
        from hr_department d
        order by d.parent_id desc
        """)
        res = cr2.fetchall()
        if res:
            _logger.info('Migrating %s departments' % len(res))
            department_old_new_ids = {}
            for r in res:
                name = r[0]
                color = r[1]
                message_last_post = r[2]
                company_id2 = r[3]
                note = r[4]
                parent_id2 = r[5]
                #manager_id2 = r[6]  # later in post employees insert
                department_id2 = r[7]

                company_id = False
                if company_id2:
                    company_id = self.IdVersion10(
                        cr2, 'res.company', ('name',), company_id2
                    )

                if parent_id2:
                    parent_id = department_old_new_ids.get(parent_id2, False)
                    if not parent_id:
                        msg = u"""Unable to fetch parent ID for department %s
                        """ % name
                        raise UserError(msg)

                vals = {
                    'name': name, 'message_last_post': message_last_post,
                    'company_id': company_id, 'note': note, 'color': color,

                }
                args = [('name', '=', name)]
                if department_obj.search_count(args):
                    department = department_obj.search(args)
                    department.ensure_one()
                    del vals['name']
                    department.write(vals)
                else:
                    department = department_obj.create(vals)
                department_old_new_ids[department_id2] = department.id

        # hr_job --------------------------------------------------------------
        job_obj = self.env['hr.job']
        cr2.execute("""
        select
            description -- 0
            ,name -- 1
            ,message_last_post -- 2
            ,company_id -- 3
            ,expected_employees -- 4
            ,state -- 5
            ,no_of_recruitment -- 6
            ,requirements -- 7
            ,no_of_hired_employee -- 8
            ,no_of_employee -- 9
            ,department_id -- 10
        from hr_job
        order by id
        """)
        res = cr2.fetchall()
        if res:
            _logger.info('Migrating %s jobs' % len(res))
            for r in res:
                description = r[0]
                name = r[1]
                message_last_post = r[2]
                company_id2 = r[3]
                expected_employees = r[4]
                state = r[5]
                no_of_recruitment = r[6]
                requirements = r[7]
                no_of_hired_employee  = r[8]
                no_of_employee = r[9]
                department_id2 = r[10]

                company_id = False
                if company_id2:
                    company_id = self.IdVersion10(
                        cr2, 'res.company', ('name',), company_id2
                    )

                department_id = False
                if department_id2:
                    department_id = department_old_new_ids.get(
                        department_id2, False
                    )

                vals = {
                    'company_id': company_id,
                    'department_id': department_id,
                    'description': description,
                    'expected_employees': expected_employees,
                    'message_last_post': message_last_post,
                    'name': name,
                    'no_of_employee': no_of_employee,
                    'no_of_hired_employee': no_of_hired_employee,
                    'no_of_recruitment': no_of_recruitment,
                    'requirements': requirements,
                    'state': state,
                }
                if job_obj.search_count([('name', '=', name)]):
                    job = job_obj.search([('name', '=', name)])
                    job.ensure_one()
                    del vals['name']
                    job.write(vals)
                else:
                    job_obj.create(vals)

        # resource_calendar ---------------------------------------------------
        rescal_obj = self.env['resource.calendar']
        cr2.execute("""
        select
            name -- 0
            ,company_id -- 1
            ,manager -- 2
            ,id -- 3
        from resource_calendar
        order by id
        """)
        res = cr2.fetchall()
        rescal_old_new_ids = {}
        if res:
            _logger.info(
                'Migrating %s resource calendars' % len(res))
            for r in res:
                name = r[0]
                company_id2 = r[1]
                manager2 = r[2]
                rescal_id2 = r[3]

                company_id = False
                if company_id2:
                    company_id = self.IdVersion10(
                        cr2, 'res.company', ('name',), company_id2
                    )

                manager = False
                if manager2:
                    if manager2 == 1:
                        manager = 1  # admin user (do not migrate)
                    else:
                        manager = self.IdVersion10(
                            cr2, 'res.users', ('login',), manager2
                        )

                vals = {
                    'name': name, 'company_id': company_id, 'manager': manager,

                }
                if rescal_obj.search_count([('name', '=', name)]):
                    rescal = rescal_obj.search([('name', '=', name)])
                    rescal.ensure_one()
                    del vals['name']
                    rescal.write(vals)
                else:
                    rescal = rescal_obj.create(vals)
                rescal_old_new_ids[rescal_id2] = rescal.id

        # resource_resource ---------------------------------------------------
        resource_obj = self.env['resource.resource']
        cr2.execute("""
        select
            active -- 0
            ,calendar_id -- 1
            ,code -- 2
            ,company_id -- 3
            ,name -- 4
            ,resource_type -- 5
            ,time_efficiency -- 6
            ,user_id -- 7
            ,id -- 8
        from resource_resource where id in (
            select distinct(resource_id) from hr_employee
            where resource_id is not null
        )
        order by id
        """)
        res = cr2.fetchall()
        if res:
            _logger.info('Migrating %s employee related resources' % len(res))
            for r in res:
                active = r[0]
                calendar_id2 = r[1]
                code = r[2]
                company_id2 = r[3]
                name = r[4]
                resource_type = r[5]
                time_efficiency = r[6]
                user_id2 = r[7]

                calendar_id = False
                if calendar_id2:
                    calendar_id = rescal_old_new_ids.get(calendar_id2, False)

                company_id = False
                if company_id2:
                    company_id = self.IdVersion10(
                        cr2, 'res.company', ('name',), company_id2
                    )

                user_id = False
                if user_id2:
                    if user_id2 == 1:
                        user_id = 1  # admin user (do not migrate)
                    else:
                        user_id = self.IdVersion10(
                            cr2, 'res.users', ('login',), user_id2
                        )

                vals = {
                    'active': active,
                    'calendar_id': calendar_id,
                    'code': code,
                    'company_id': company_id,
                    'name': name,
                    'resource_type': resource_type,
                    'time_efficiency': time_efficiency,
                    'user_id': user_id,

                }
                if resource_obj.search_count([('name', '=', name)]):
                    del vals['name']
                    resource = resource_obj.search([('name', '=', name)])
                    resource.ensure_one()
                    resource.write(vals)
                else:
                    resource_obj.create(vals)

        return True

    # -----------------------------------------------------------------
    # Employees
    # -----------------------------------------------------------------
    @api.model
    def Employees(self, cr2):
        employee_obj = self.env['hr.employee']
        cr2.execute("""select id from hr_employee order by id""")
        employee_ids2 = [i[0] for i in cr2.fetchall() if i and i[0] or False]
        if not employee_ids2:
            raise UserError(
                """Unable to fetch employees from %s""" % self.other_db_name
            )
        c, employee_old_new_ids, parent_ids2, coach_ids2 = 0, {}, [], []
        for employee_id2 in employee_ids2:
            c += 1
            _logger.debug(
                'Migrating %s/%s employees' % (c, len(employee_ids2))
            )

            vals = self.EmployeeVals9(cr2, employee_id2)
            parent_id2 = vals.get('parent_id2', False)
            if parent_id2 and parent_id2 not in parent_ids2:
                parent_ids2.append(parent_id2)
            del vals['parent_id2']

            coach_id2 = vals.get('coach_id2', False)
            if coach_id2 and coach_id2 not in coach_ids2:
                coach_ids2.append(coach_id2)
            del vals['coach_id2']

            resource_id = vals.get('resource_id', False)
            assert resource_id, 'Need resource_id here'

            args = [('resource_id', '=', resource_id)]
            if not employee_obj.search_count(args):
                try:
                    employee = employee_obj.create(vals)
                except Exception, err:
                    raise UserError(err)
                employee_old_new_ids[employee_id2] = employee.id

        _logger.debug('Updating %s employee parent_id' % len(parent_ids2))
        for parent_id2 in parent_ids2:
            parent_id = employee_old_new_ids.get(parent_id2, False)
            if not parent_id:
                continue

            cr2.execute("""select id from hr_employee where parent_id = %s
            """ % parent_id2)
            ids2 = [i[0] for i in cr2.fetchall() if i and i[0] or False]
            assert ids2, 'Need res_ids here'

            ids = [employee_old_new_ids.get(i, False) for i in ids2]
            assert ids, 'Need ids here'

            employees = employee_obj.browse(ids)
            employees.write({'parent_id': parent_id})

        _logger.debug('Updating %s employee coach_id' % len(coach_ids2))
        for coach_id2 in coach_ids2:
            coach_id = employee_old_new_ids.get(coach_id2, False)
            if not coach_id:
                continue

            cr2.execute("""select id from hr_employee where coach_id = %s
            """ % coach_id2)
            ids2 = [i[0] for i in cr2.fetchall() if i and i[0] or False]
            assert ids2, 'Need res_ids here'

            ids = [employee_old_new_ids.get(i, False) for i in ids2]
            assert ids, 'Need ids here'

            employees = employee_obj.browse(ids)
            employees.write({'coach_id': coach_id})

        return True

    @api.model
    def EmployeeVals9(self, cr2, employee_id2):
        """
        Fetches employees from old database and prepares dict to create()
        or write() on new database
        :param cr2: cursor to old database
        :param employee_id2: int, old database employee record ID
        :return: dict
        """
        sql = """
        select
            address_home_id -- 0
            ,address_id -- 1
            ,bank_account_id -- 2
            ,birthday -- 3
            ,children -- 4
            ,coach_id -- 5
            ,color -- 6
            ,country_id -- 7
            ,department_id -- 8
            ,gender -- 9
            ,identification_id -- 10
            ,job_id -- 11
            ,manager -- 12
            ,marital -- 13
            ,medic_exam -- 14
            ,message_last_post -- 15
            ,mobile_phone -- 16
            ,name_related -- 17
            ,notes -- 18
            ,parent_id -- 19
            ,passport_id -- 20
            ,place_of_birth -- 21
            ,resource_id -- 22
            ,sinid -- 23
            ,ssnid -- 24
            ,timesheet_cost -- 25
            ,vehicle -- 26
            ,vehicle_distance -- 27
            ,work_email -- 28
            ,work_location -- 29
            ,work_phone -- 30
        from hr_employee where id = %s
        """ % employee_id2
        cr2.execute(sql)
        res = cr2.fetchall()
        if not res:
            raise UserError(_("""Unable to fetch employees
            from %s (ID %s)""") % (self.other_db_name, employee_id2))
        vals = {}
        for r in res:
            address_home_id2 = r[0]
            address_id2 = r[1]
            bank_account_id2 = r[2]
            birthday = r[3]
            children = r[4]
            coach_id2 = r[5]
            color = r[6]
            country_id2 = r[7]
            department_id2 = r[8]
            gender = r[9]
            identification_id = r[10]  # this is char
            job_id2 = r[11]
            manager = r[12]
            marital = r[13]
            medic_exam = r[14]
            message_last_post = r[15]
            mobile_phone = r[16]
            name_related = r[17]
            notes = r[18]
            parent_id2 = r[19]
            passport_id = r[20]  # this is char
            place_of_birth = r[21]
            resource_id2 = r[22]
            sinid = r[23]
            ssnid = r[24]
            timesheet_cost = r[25]
            vehicle = r[26]
            vehicle_distance = r[27]
            work_email = r[28]
            work_location = r[29]
            work_phone = r[30]

            address_home_id = False
            if address_home_id2:
                if address_home_id2 == 3:
                    address_home_id = 3
                else:
                    address_home_id = self.IdVersion10(cr2, 'res.partner',
                        ('name', 'vat', 'nrc', 'company_id', 'is_company'),
                        address_home_id2
                    )

            address_id = False
            if address_id2:
                if address_id2 == 1:
                    address_id = 1
                else:
                    address_id = self.IdVersion10(cr2, 'res.partner',
                        ('name', 'vat', 'nrc', 'company_id', 'is_company'),
                        address_id2
                    )

            bank_account_id = False
            if bank_account_id2:
                bank_account_id = self.IdVersion10(
                    cr2, 'res.partner.bank', ('sanitized_acc_number',),
                    bank_account_id2
                )

            country_id = False
            if country_id2:
                if country_id2 == 254:
                    country_id2 = 190
                country_id = self.IdVersion10(
                    cr2, 'res.country', ('code', 'name'), country_id2
                )

            department_id = False
            if department_id2:
                department_id = self.IdVersion10(
                    cr2, 'hr.department', ('name',), department_id2
                )

            job_id = False
            if job_id2:
                job_id = self.IdVersion10(
                    cr2, 'hr.job', ('name',), job_id2
                )

            resource_id = self.IdVersion10(
                    cr2, 'resource.resource', ('name', 'active'),
                    resource_id2
                )

            vals.update({
                'address_home_id': address_home_id,
                'address_id': address_id,
                'bank_account_id': bank_account_id,
                'birthday': birthday,
                'children': children,
                'coach_id2': coach_id2,
                'color': color,
                'country_id': country_id,
                'department_id': department_id,
                'gender': gender,
                'identification_id': identification_id,
                'job_id': job_id,
                'manager': manager,
                'marital': marital,
                'medic_exam': medic_exam,
                'message_last_post': message_last_post,
                'mobile_phone': mobile_phone,
                'name_related': name_related,
                'notes': notes,
                'parent_id2': parent_id2,
                'passport_id': passport_id,
                'place_of_birth': place_of_birth,
                'resource_id': resource_id,
                'sinid': sinid,
                'ssnid': ssnid,
                'timesheet_cost': timesheet_cost,
                'vehicle': vehicle,
                'vehicle_distance': vehicle_distance,
                'work_email': work_email,
                'work_location': work_location,
                'work_phone': work_phone,
            })
            break

        return vals

    @api.model
    def EmployeesPost(self, cr2):
        raise UserError('Nothing to do here')
