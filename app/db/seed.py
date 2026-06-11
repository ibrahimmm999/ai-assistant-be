import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.models import Product, Audience, Campaign, PerformanceMetric

def seed_database(db: Session):
    has_data = db.query(Product).first()
    if has_data:
        print("Database already seeded. Skipping initial data population.")
        return

    # SEED AUDIENCES
    audiences_data = [
        Audience(name="Gen Z Tech Savvy", segment_size=150000, description="Pengguna aktif TikTok & Instagram, menyukai produk viral."),
        Audience(name="Millennial Working Moms", segment_size=85000, description="Ibu bekerja usia 25-40 tahun, fokus pada skincare premium."),
        Audience(name="Male Grooming Enthusiasts", segment_size=45000, description="Pria perkotaan yang peduli penampilan & kepraktisan."),
        Audience(name="Budget Beauty Shoppers", segment_size=200000, description="Pemburu diskon, sensitif harga, kosmetik di bawah 100k."),
        Audience(name="Eco-Conscious Consumers", segment_size=30000, description="Konsumen hijau, mencari produk vegan & cruelty-free."),
        Audience(name="Luxury Skincare Lovers", segment_size=25000, description="Konsumen loyal brand high-end dengan hasil teruji.")
    ]
    db.add_all(audiences_data)
    db.commit()

    # SEED PRODUCTS
    products_data = [
        Product(name="Wardah Lightening Serum", category="Skincare", price=65000, target_generation="Gen Z"),
        Product(name="Wardah Crystal Secret Cream", category="Skincare", price=95000, target_generation="Millennials"),
        Product(name="Emina Bright Stuff Face Wash", category="Skincare", price=28000, target_generation="Gen Z"),
        Product(name="Emina Sun Battle SPF 30", category="Skincare", price=35000, target_generation="Gen Z"),
        Product(name="Somethinc Niacinamide Moisture", category="Skincare", price=119000, target_generation="Gen Z"),
        Product(name="Somethinc Retinol Alternative", category="Skincare", price=155000, target_generation="Millennials"),
        Product(name="Kahf Face Wash Oil Control", category="Skincare", price=38000, target_generation="Gen Z"),
        Product(name="Kahf All-in-One Body Wash", category="Skincare", price=42000, target_generation="Gen Z"),
        Product(name="HMS Matte Lip Cream", category="Makeup", price=59000, target_generation="Gen Z"),
        Product(name="Luxcrime Setting Spray", category="Makeup", price=79000, target_generation="Gen Z"),
        Product(name="ESQA Flawless Cushion", category="Makeup", price=185000, target_generation="Millennials"),
        Product(name="Avoskin Miraculous Toner", category="Skincare", price=189000, target_generation="Millennials"),
        Product(name="Skintific 5X Ceramide Gel", category="Skincare", price=139000, target_generation="Gen Z"),
        Product(name="Anessa Perfect UV Sunscreen", category="Skincare", price=330000, target_generation="Millennials"),
        Product(name="Garnier Micellar Water", category="Skincare", price=45000, target_generation="Gen Z")
    ]
    db.add_all(products_data)
    db.commit()

    all_audiences = db.query(Audience).all()
    all_products = db.query(Product).all()

    # SEED CAMPAIGNS
    campaign_themes = ["Ramadhan Eid Sales", "11.11 Mega Shopping", "12.12 Year End Festive", "Payday Special Flash", "Glow Up Project", "Back To Campus Promo"]
    channels = ["TikTok Ads", "Instagram Paid", "Shopee Live", "Google Search"]

    campaigns_pool = []
    for i in range(1, 41):
        theme = random.choice(campaign_themes)
        channel = random.choice(channels)
        prod = random.choice(all_products)
        aud = random.choice(all_audiences)
        
        camp_name = f"CMP-2026-{i:02d} | {theme} ({channel})"
        budget = float(random.randint(5, 75) * 1000000)
        
        camp = Campaign(
            name=camp_name,
            budget=budget,
            product_id=prod.id,
            audience_id=aud.id
        )
        db.add(camp)
        campaigns_pool.append(camp)
        
    db.commit()

    # SEED PERFORMANCE METRICS
    base_date = datetime(2026, 3, 1)

    for i in range(1, 61):
        camp = random.choice(campaigns_pool)
        record_date = base_date + timedelta(days=random.randint(1, 30))
        
        clicks = random.randint(1200, 25000)
        conversion_rate = random.uniform(0.015, 0.065)
        conversions = int(clicks * conversion_rate)
        revenue = float(conversions * random.randint(60000, 110000))
        
        metric = PerformanceMetric(
            campaign_id=camp.id,
            date=record_date.date(),
            clicks=clicks,
            conversions=conversions,
            revenue=revenue
        )
        db.add(metric)
        
    db.commit()
    print("Database seeding completed successfully. 15 Products, 6 Audiences, 40 Campaigns, and 60 Metrics loaded.")