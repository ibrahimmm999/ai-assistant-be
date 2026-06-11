import pytest
from app.services.ai_service import is_query_safe
import inspect
from app.services.ai_service import is_query_safe

class TestReadOnlyEnforcement:
    def test_select_is_allowed(self):
        """Query SELECT biasa harus diizinkan."""
        assert is_query_safe("SELECT id, name FROM products LIMIT 10;") is True

    def test_with_cte_is_allowed(self):
        """CTE yang diawali WITH harus diizinkan."""
        sql = "WITH top AS (SELECT * FROM campaigns ORDER BY budget DESC) SELECT * FROM top LIMIT 5;"
        assert is_query_safe(sql) is True

    def test_drop_is_blocked(self):
        """DROP TABLE harus diblokir."""
        assert is_query_safe("DROP TABLE products;") is False

    def test_delete_is_blocked(self):
        """DELETE harus diblokir meskipun dikombinasikan dengan SELECT."""
        assert is_query_safe("SELECT * FROM campaigns; DELETE FROM campaigns WHERE id = 1;") is False

    def test_update_is_blocked(self):
        """UPDATE harus diblokir."""
        assert is_query_safe("UPDATE products SET price = 0 WHERE id = 5;") is False

    def test_insert_is_blocked(self):
        """INSERT harus diblokir."""
        assert is_query_safe("INSERT INTO products (name) VALUES ('fake');") is False

    def test_alter_is_blocked(self):
        """ALTER TABLE harus diblokir."""
        assert is_query_safe("ALTER TABLE products ADD COLUMN hacked TEXT;") is False

    def test_truncate_is_blocked(self):
        """TRUNCATE harus diblokir."""
        assert is_query_safe("TRUNCATE TABLE campaigns;") is False

    def test_grant_is_blocked(self):
        """GRANT harus diblokir."""
        assert is_query_safe("GRANT ALL PRIVILEGES ON products TO hacker;") is False

    def test_revoke_is_blocked(self):
        """REVOKE harus diblokir."""
        assert is_query_safe("REVOKE SELECT ON products FROM public;") is False


class TestTableWhitelist:
    def test_known_table_products_allowed(self):
        """Query ke tabel products harus diizinkan."""
        assert is_query_safe("SELECT * FROM products LIMIT 10;") is True

    def test_known_table_audiences_allowed(self):
        """Query ke tabel audiences harus diizinkan."""
        assert is_query_safe("SELECT * FROM audiences LIMIT 10;") is True

    def test_known_table_campaigns_allowed(self):
        """Query ke tabel campaigns harus diizinkan."""
        assert is_query_safe("SELECT * FROM campaigns LIMIT 10;") is True

    def test_known_table_performance_metrics_allowed(self):
        """Query ke tabel performance_metrics harus diizinkan."""
        assert is_query_safe("SELECT * FROM performance_metrics LIMIT 10;") is True

    def test_unknown_table_blocked(self):
        """Query ke tabel tidak dikenal harus diblokir."""
        assert is_query_safe("SELECT * FROM system_users;") is False

    def test_unknown_table_pg_internal_blocked(self):
        """Query ke tabel internal PostgreSQL harus diblokir."""
        assert is_query_safe("SELECT * FROM pg_user;") is False

    def test_join_known_tables_allowed(self):
        """JOIN antara tabel yang dikenal harus diizinkan."""
        sql = """
            SELECT p.name, c.budget 
            FROM products p 
            JOIN campaigns c ON p.id = c.product_id 
            LIMIT 10;
        """
        assert is_query_safe(sql) is True

    def test_join_with_unknown_table_blocked(self):
        """JOIN yang melibatkan tabel tidak dikenal harus diblokir."""
        sql = "SELECT * FROM products JOIN secret_table ON products.id = secret_table.id;"
        assert is_query_safe(sql) is False

class TestEdgeCases:
    def test_case_insensitive_forbidden_token(self):
        """Forbidden token huruf kecil tetap harus diblokir."""
        assert is_query_safe("select * from products; delete from products;") is False

    def test_empty_string_is_blocked(self):
        """String kosong harus diblokir."""
        assert is_query_safe("") is False

    def test_non_sql_string_is_blocked(self):
        """String bukan SQL harus diblokir."""
        assert is_query_safe("hello world") is False

    def test_subquery_known_tables_allowed(self):
        """Subquery yang menggunakan tabel dikenal harus diizinkan."""
        sql = """
            SELECT * FROM campaigns 
            WHERE product_id IN (SELECT id FROM products WHERE price < 100000)
            LIMIT 10;
        """
        assert is_query_safe(sql) is True