import mysql.connector
from mysql.connector import Error
from datetime import datetime

class EmailLogsManagerV2:
    def __init__(self, hostname, username, password, database, pool_name="mypool", pool_size=5):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.database = database
        self.pool_name = pool_name
        self.pool_size = pool_size
        self.conn_pool = None

        self.create_pool()

    def create_pool(self):
        try:
            self.conn_pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name=self.pool_name,
                pool_size=self.pool_size,
                pool_reset_session=True,
                host=self.hostname,
                user=self.username,
                password=self.password,
                database=self.database
            )
            print("Connection pool created successfully.")
        except Error as e:
            print(f"Error creating connection pool: {e}")

    def get_connection(self):
        try:
            return self.conn_pool.get_connection()
        except Error as e:
            print(f"Error getting connection from pool: {e}")
            return None

    def close_connection(self, conn):
        if conn is not None and conn.is_connected():
            conn.close()
            print("Connection returned to pool.")

    def execute_query(self, query, params=None, fetch=False):
        conn = self.get_connection()
        if conn is None:
            return None

        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            if fetch:
                result = cursor.fetchall()
                return result
            conn.commit()
        except Error as e:
            print(f"Error executing query: {e}")
            return None
        finally:
            if 'cursor' in locals():
                cursor.close()
            self.close_connection(conn)

    def insert_email_log(self, email_data, classification, classify_by, user_id):
        try:
            # cursor = self.conn.cursor()

            # Lấy dữ liệu từ email_data
            mail_id = email_data.get('id', '')
            if mail_id == '':
                return
            
            created_datetime = email_data.get('createdDateTime', '')
            last_modified_datetime = email_data.get('lastModifiedDateTime', '')
            received_datetime = email_data.get('receivedDateTime', '')
            subject = email_data.get('subject', '')
            body_preview = email_data.get('bodyPreview', '')
            is_read = email_data.get('isRead', '')
            body_content = email_data.get('body', {}).get('content', '')
            
            sender_email_address = email_data.get('sender', {}).get('emailAddress', {}).get('address', '')
            sender_name = email_data.get('sender', {}).get('emailAddress', {}).get('name', '')

            from_email_address = email_data.get('from', {}).get('emailAddress', {}).get('address', '')
            from_name = email_data.get('from', {}).get('emailAddress', {}).get('name', '')
            
            to_recipient_email_address = email_data.get('toRecipients', [{}])[0].get('emailAddress', {}).get('address', '')
            to_recipient_name = email_data.get('toRecipients', [{}])[0].get('emailAddress', {}).get('name', '')
            
            # Dữ liệu từ dự đoán, phân loại, v.v.
            # classification = 'Phishing' #email_data.get('inferenceClassification', '')
            # classify_by = 'LSTM'#email_data.get('classifyBy', '')
            click = email_data.get('flag', {}).get('flagStatus', '') == 'flagged'

            # Query insert
            insert_query = """
                INSERT INTO email_logs (
                    mailId, createdDateTime, lastModifiedDateTime, receivedDateTime, subject,
                    bodyPreview, isRead, bodyContent, senderEmailAddress, senderName, fromEmailAddress, fromName,
                    toRecipientEmailAddress, toRecipientName, data, classification, classifyBy, click, userId
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            insert_values = (
                mail_id, created_datetime, last_modified_datetime, received_datetime, subject,
                body_preview, is_read, body_content, sender_email_address, sender_name, from_email_address, from_name,
                to_recipient_email_address, to_recipient_name, str(email_data), classification, classify_by, click, user_id
            )
            
            # cursor.execute(insert_query, insert_values)
            # self.conn.commit()
            self.execute_query(insert_query, insert_values)
            print(f"Đã insert email {mail_id} vào bảng email_logs thành công.")
            
        except Error as e:
            print(f"Lỗi khi insert email: {e}")

        # finally:
        #     if 'cursor' in locals():
        #         cursor.close()

    def update_email_log(self, email_id, email_data, email_exist, classifyBy, classification):
        try:
            # cursor = self.conn.cursor()
            # Lấy dữ liệu từ email_data
            mail_id = email_data.get('id', '')
            created_datetime = email_data.get('createdDateTime', '')
            last_modified_datetime = email_data.get('lastModifiedDateTime', '')
            received_datetime = email_data.get('receivedDateTime', '')
            subject = email_data.get('subject', '')
            body_preview = email_data.get('bodyPreview', '')
            is_read = email_data.get('isRead', '')
            body_content = email_data.get('body', {}).get('content', '')
            
            sender_email_address = email_data.get('sender', {}).get('emailAddress', {}).get('address', '')
            sender_name = email_data.get('sender', {}).get('emailAddress', {}).get('name', '')

            from_email_address = email_data.get('from', {}).get('emailAddress', {}).get('address', '')
            from_name = email_data.get('from', {}).get('emailAddress', {}).get('name', '')
            
            to_recipient_email_address = email_data.get('toRecipients', [{}])[0].get('emailAddress', {}).get('address', '')
            to_recipient_name = email_data.get('toRecipients', [{}])[0].get('emailAddress', {}).get('name', '')
            currentClassification = email_exist.get('classification')
            user_id = email_exist.get('userId')
            # Dữ liệu từ dự đoán, phân loại, v.v.
            # classification = classification #email_data.get('inferenceClassification', '')
            classification_of_user = email_exist.get('classificationOfUser')
            classify_by_manual = None#email_data.get('classifyBy', '')
            print("==========3=3========", email_data.get('categories', []))
            # print("==========4=4========", email_data)
            # if 'Phishing' in email_data.get('categories', []) and (currentClassification != 'Phishing' or classification_of_user != 'Phishing'):
            if ('Phishing' in email_data.get('categories', []) and currentClassification != 'Phishing') or (classification_of_user == 'Legit' and 'Phishing' in email_data.get('categories', [])):
                classification_of_user = 'Phishing'
                classify_by_manual = 'USER'
            elif 'Phishing' not in email_data.get('categories', []) and currentClassification == 'Phishing':
                classification_of_user = 'Legit'
                classify_by_manual = 'USER'
            click = email_data.get('flag', {}).get('flagStatus', '') == 'flagged'

            # Update query
            update_query = """
                UPDATE email_logs 
                SET createdDateTime = %s,
                    lastModifiedDateTime = %s,
                    receivedDateTime = %s,
                    subject = %s,
                    bodyPreview = %s,
                    isRead = %s,
                    bodyContent = %s,
                    senderEmailAddress = %s,
                    senderName = %s,
                    fromEmailAddress = %s,
                    fromName = %s,
                    toRecipientEmailAddress = %s,
                    toRecipientName = %s,
                    data = %s,
                    classificationOfUser = %s,
                    classifyByManual = %s,
                    click = %s,
                    userId = %s
                WHERE mailId = %s
            """
            update_values = (
                created_datetime, last_modified_datetime, 
                received_datetime, subject,
                body_preview, is_read, body_content, sender_email_address, sender_name, from_email_address, from_name,
                to_recipient_email_address, to_recipient_name, str(email_data), classification_of_user, classify_by_manual, click, user_id, 
                mail_id
            )
            # print(update_values)
            self.execute_query(update_query, update_values)
            
            # cursor.execute(update_query, update_values)
            # self.conn.commit()
            # print(f"Đã cập nhật email {email_id} trong bảng email_logs thành công.")
            
        except Error as e:
            print(f"Lỗi khi cập nhật email: {e}")

        # finally:
        #     if 'cursor' in locals():
        #         cursor.close()

    def check_email_exists(self, mail_id):
        try:
            cursor = self.conn.cursor()

            # Query kiểm tra email tồn tại
            check_query = """
                SELECT COUNT(*)
                FROM email_logs
                WHERE mailId = %s
            """
            cursor.execute(check_query, (mail_id,))
            result = cursor.fetchone()

            if result and result[0] > 0:
                # print(f"Email có mailId {mail_id} đã tồn tại trong bảng email_logs.")
                return True
            else:
                # print(f"Email có mailId {mail_id} chưa tồn tại trong bảng email_logs.")
                return False
            
        except Error as e:
            print(f"Lỗi khi kiểm tra email: {e}")
            return False

        finally:
            if 'cursor' in locals():
                cursor.close()

    def count_total_emails(self):
        try:
            # cursor = self.conn.cursor()
            # cursor = self.get_cursor()
            # print("cursor", cursor)
            # Query đếm số lượng email
            count_query = """
                SELECT COUNT(*)
                FROM email_logs
            """
            # cursor.execute(count_query)
            # result = cursor.fetchone()
            result = self.execute_query(count_query, fetch=True)   
            # print("result", result)
            if result:
                total_emails = result[0]['COUNT(*)']
                # print(f"Tổng số lượng email trong bảng email_logs là: {total_emails}")
                return total_emails
            else:
                # print("Không có email nào trong bảng email_logs.")
                return 0
            
        except Error as e:
            print(f"Lỗi khi đếm số lượng email: {e}")
            return 0

        # finally:
        #     if 'cursor' in locals():
        #         # print("900909090======+++++++==")
        #         cursor.close()

    def count_total_phishing_emails(self):
        try:
            # cursor = self.conn.cursor()
            # cursor = self.get_cursor()
            # Query đếm số lượng email
            count_query = """
                SELECT COUNT(*)
                FROM email_logs
                WHERE classification = 'Phishing' AND (classifyByManual is null)
            """
            # cursor.execute(count_query)
            # result = cursor.fetchone()
            result = self.execute_query(count_query, fetch=True)   

            if result:
                total_emails = result[0]['COUNT(*)']
                print(f"Tổng số lượng phishing email trong bảng email_logs là: {total_emails}")
                return total_emails
            else:
                # print("Không có phishing email nào trong bảng email_logs.")
                return 0
            
        except Error as e:
            # print(f"Lỗi khi đếm số lượng phishing email: {e}")
            return 0

        # finally:
        #     if 'cursor' in locals():
        #         cursor.close()

    def count_total_unlabeling_emails_by_user(self):
        try:
            # cursor = self.conn.cursor()
            # cursor = self.get_cursor()
            # Query đếm số lượng phishing email đã đọc
            count_query = """
                SELECT COUNT(*)
                FROM email_logs
                WHERE classificationOfUser = 'Legit' AND classifyByManual = 'USER'
            """
            # cursor.execute(count_query)
            # result = cursor.fetchone()
            result = self.execute_query(count_query, fetch=True)   

            if result:
                total_emails = result[0]['COUNT(*)']
                # print(f"Tổng số lượng phishing email đã đọc trong bảng email_logs là: {total_emails}")
                return total_emails
            else:
                # print("Không có phishing email đã đọc nào trong bảng email_logs.")
                return 0
            
        except Error as e:
            print(f"Lỗi khi đếm số lượng phishing email đã đọc: {e}")
            return 0

        # finally:
        #     if 'cursor' in locals():
        #         cursor.close()

    def count_total_phishing_is_read_emails(self):
        try:
            # cursor = self.conn.cursor()
            # cursor = self.get_cursor()
            # Query đếm số lượng phishing email đã đọc
            count_query = """
                SELECT COUNT(*)
                FROM email_logs
                WHERE classification = 'phishing' AND isRead = 1
            """
            # cursor.execute(count_query)
            # result = cursor.fetchone()
            result = self.execute_query(count_query, fetch=True)     

            if result:
                total_emails = result[0]['COUNT(*)']
                # print(f"Tổng số lượng phishing email đã đọc trong bảng email_logs là: {total_emails}")
                return total_emails
            else:
                # print("Không có phishing email đã đọc nào trong bảng email_logs.")
                return 0
            
        except Error as e:
            print(f"Lỗi khi đếm số lượng phishing email đã đọc: {e}")
            return 0

        # finally:
        #     if 'cursor' in locals():
        #         cursor.close()

    def count_total_phishing_emails_by_user(self):
        try:
            # cursor = self.conn.cursor()
            # cursor = self.get_cursor()
            # Query đếm số lượng phishing email by user
            count_query = """
                SELECT COUNT(*)
                FROM email_logs
                WHERE classification = 'Legit' AND classifyByManual = 'USER' AND classificationOfUser = 'Phishing'
            """
            # cursor.execute(count_query)
            # result = cursor.fetchone()
            result = self.execute_query(count_query, fetch=True)     

            if result:
                total_emails = result[0]['COUNT(*)']
                # print(f"Tổng số lượng phishing email by user trong bảng email_logs là: {total_emails}")
                return total_emails
            else:
                # print("Không có phishing email by user nào trong bảng email_logs.")
                return 0
            
        except Error as e:
            print(f"Lỗi khi đếm số lượng phishing email by user: {e}")
            return 0

        # finally:
        #     if 'cursor' in locals():
        #         cursor.close()
   
    def get_emails_ordered_by_received_datetime(self, top):
        try:
            # cursor = self.conn.cursor()

            # Query lấy danh sách email từ mới đến cũ
            select_query = """
                SELECT mailId, createdDateTime, lastModifiedDateTime, receivedDateTime, subject,
                bodyPreview, isRead, bodyContent, senderEmailAddress, senderName, 
                fromEmailAddress, fromName, toRecipientEmailAddress, toRecipientName, 
                classification, classificationOfUser, classifyBy, click, classifyByUser, classifyByManual
                FROM email_logs
                ORDER BY receivedDateTime DESC
            """

            if top:
                select_query = f"""
                    SELECT mailId, createdDateTime, lastModifiedDateTime, receivedDateTime, subject,
                    bodyPreview, isRead, bodyContent, senderEmailAddress, senderName, 
                    fromEmailAddress, fromName, toRecipientEmailAddress, toRecipientName, 
                    classification, classificationOfUser, classifyBy, click, classifyByUser, classifyByManual
                    FROM email_logs
                    ORDER BY receivedDateTime DESC
                    LIMIT {top}
                """
            # print('select_query', select_query)
            # cursor.execute(select_query)
            emails = self.execute_query(query=select_query, fetch=True)
            # print("emails", emails)
            # Convert fetched data to JSON format
            email_list = []
            for email in emails:
                classifyByUser = email.get('classifyByUser', '')
                if email.get('classifyByManual', '') == 'USER':
                    classifyByUser = email.get('toRecipientName', '')

                email_dict = {
                    'mailId': email.get('mailId', ''),
                    'createdDateTime': email.get('createdDateTime', ''),
                    'lastModifiedDateTime': email.get('lastModifiedDateTime', ''),
                    'receivedDateTime': email.get('receivedDateTime', ''),
                    'subject': email.get('subject', ''),
                    'bodyPreview': email.get('bodyPreview', ''),
                    'isRead': bool(email.get('isRead', '')),
                    'bodyContent': email.get('bodyContent', ''),
                    'senderEmailAddress': email.get('senderEmailAddress', ''),
                    'senderName': email.get('senderName', ''),
                    'fromEmailAddress': email.get('fromEmailAddress', ''),
                    'fromName': email.get('fromName', ''),
                    'toRecipientEmailAddress': email.get('toRecipientEmailAddress', ''),
                    'toRecipientName': email.get('toRecipientName', ''),
                    # 'data': email[14],
                    'classification': email.get('classification', ''),
                    'classificationOfUser': '' if email.get('classificationOfUser', '') == None else email.get('classificationOfUser', ''),
                    'classifyBy': email.get('classifyBy', ''),
                    'click': bool(email.get('click', '')),
                    'classifyByUser': '' if classifyByUser == None else classifyByUser,
                    # Add other fields as needed
                }
                email_list.append(email_dict)

            if email_list:
                # for email in emails:
                #     # print(email)  # In thông tin email hoặc xử lý tiếp theo nếu cần
                return email_list
            else:
                # print("Không có email nào trong bảng email_logs.")
                return []

        except Error as e:
            print(f"Lỗi khi lấy danh sách email: {e}")
            return []

        # finally:
        #     if 'cursor' in locals():
        #         cursor.close()

    def get_email_by_mail_id(self, mail_id):
        try:
            # cursor = self.conn.cursor(dictionary=True)

            # Step 2: Fetch data from database
            select_query = """
                SELECT id, mailId, createdDateTime, lastModifiedDateTime, receivedDateTime, subject, bodyPreview, isRead,
                    bodyContent, senderEmailAddress, senderName, fromEmailAddress, fromName, toRecipientEmailAddress, 
                    toRecipientName, data, classification, classificationOfUser, classifyBy, click, userId, classifyByUser, classifyByManual
                FROM email_logs
                WHERE mailId = %s
            """
            # print("select_query", select_query)

            # cursor.execute(select_query, (mail_id,))
            # email_data = cursor.fetchone()
            # Step 3: Instantiate the Email object
            email_data = self.execute_query(query=select_query, params=(mail_id,), fetch=True)
            if email_data:
                # print(email_data[0])
                return email_data[0]
            else:
                print("No email found with the provided mail_id")
                return None

        except Error as e:
            print(f"Lỗi khi lấy chi tiết email: {e}")
            return None

        # finally:
        #     if 'cursor' in locals():
        #         cursor.close()

    def get_total_emails_by_date(self):
        try:
            # cursor = self.conn.cursor(dictionary=True)
            query = """
                SELECT DATE(receivedDateTime) AS date, COUNT(*) AS total
                FROM email_logs
                GROUP BY DATE(receivedDateTime)
                ORDER BY date
            """
            # cursor.execute(query)
            # result = cursor.fetchall()
            result = self.execute_query(query, fetch=True)
            return result
        except Error as e:
            print(f"Lỗi khi lấy tổng số email theo ngày: {e}")
            return []
        # finally:
        #     if cursor:
        #         cursor.close()

    def get_phishing_emails_by_date(self):
        try:
            # cursor = self.conn.cursor(dictionary=True)
            query = """
                SELECT DATE(receivedDateTime) AS date, COUNT(*) AS total
                FROM email_logs
                WHERE classification = 'Phishing'
                GROUP BY DATE(receivedDateTime)
                ORDER BY date
            """
            # cursor.execute(query)
            # result = cursor.fetchall()
            result = self.execute_query(query, fetch=True)
            return result
        except Error as e:
            print(f"Lỗi khi lấy tổng số email phishing theo ngày: {e}")
            return []
        # finally:
        #     if cursor:
        #         cursor.close()

    def get_phishing_email_opens_by_date(self):
        try:
            # cursor = self.conn.cursor(dictionary=True)
            query = """
                SELECT DATE(receivedDateTime) AS date, COUNT(*) AS total
                FROM email_logs
                WHERE classification = 'Phishing' AND isRead = 1
                GROUP BY DATE(receivedDateTime)
                ORDER BY date
            """
            # cursor.execute(query)
            # result = cursor.fetchall()
            result = self.execute_query(query, fetch=True)

            return result
        except Error as e:
            print(f"Lỗi khi lấy tổng số lần mở email phishing theo ngày: {e}")
            return []
        # finally:
        #     if cursor:
        #         cursor.close()

    def get_reported_emails_by_date(self):
        try:
            # cursor = self.conn.cursor(dictionary=True)
            query = """
                SELECT DATE(receivedDateTime) AS date, COUNT(*) AS total
                FROM email_logs
                WHERE classifyByManual = 'USER'
                GROUP BY DATE(receivedDateTime)
                ORDER BY date
            """
            # cursor.execute(query)
            # result = cursor.fetchall()
            result = self.execute_query(query, fetch=True)

            return result
        except Error as e:
            print(f"Lỗi khi lấy tổng số email được báo cáo theo ngày: {e}")
            return []
        # finally:
        #     if cursor:
        #         cursor.close()

    def get_email_count_by_model(self):
        try:
            # cursor = self.conn.cursor(dictionary=True)
            query = """
                SELECT classifyBy AS model, COUNT(*) AS total
                FROM email_logs
                WHERE classifyBy IN ('LSTM', 'GPT-3.5-TURBO', 'GPT-4', 'NAIVE-BAYES', 'GRU')
                GROUP BY classifyBy
            """
            # cursor.execute(query)
            # result = cursor.fetchall()
            result = self.execute_query(query, fetch=True)

            return result
        except Error as e:
            print(f"Lỗi khi lấy số lượng email theo model: {e}")
            return []
        # finally:
        #     if cursor:
        #         cursor.close()

    def get_top_users_with_phishing_emails(self, top_n=5):
        try:
            # cursor = self.conn.cursor(dictionary=True)
            query = """
                SELECT toRecipientEmailAddress, toRecipientName, COUNT(*) AS total
                FROM email_logs
                WHERE classification = 'Phishing'
                GROUP BY toRecipientEmailAddress, toRecipientName
                ORDER BY total DESC
                LIMIT %s
            """
            # cursor.execute(query, (top_n,))
            # result = cursor.fetchall()
            result = self.execute_query(query, (top_n,), fetch=True)

            return result
        except Error as e:
            print(f"Lỗi khi lấy top người dùng có số lượng email phishing nhiều nhất: {e}")
            return []
        # finally:
        #     if cursor:
        #         cursor.close()
    
    def clasify_email(self, email_id, classifyByManual, classifyByUser, classificationOfUser):
        try:
            # print(email_id)
            # print(classifyBy)
            # print(classificationOfUser)
            # cursor = self.conn.cursor()
            # Update query
            update_query = """
                UPDATE email_logs 
                SET 
                    classificationOfUser = %s,
                    classifyByManual = %s,
                    classifyByUser = %s
                WHERE mailId = %s
            """
            update_values = (
                classificationOfUser, classifyByManual, classifyByUser, email_id
            )
            
            # cursor.execute(update_query, update_values)
            # self.conn.commit()
            # print(f"Đã cập nhật email {email_id} trong bảng email_logs thành công.")
            self.execute_query(update_query, update_values)
        except Error as e:
            print(f"Lỗi khi cập nhật email: {e}")

        # finally:
        #     if 'cursor' in locals():
        #         cursor.close()
