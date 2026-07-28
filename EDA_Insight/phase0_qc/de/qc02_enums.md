# QC0.2 — Enum values cac cot phan loai

CHI DOC. Cot khong ton tai o bang do bi bo qua.


## customers.gender
- distinct: 3 | null: 0 (0.000%)
  - `Female`: 59,640 (48.91%)
  - `Male`: 57,457 (47.12%)
  - `Non-binary`: 4,833 (3.96%)

## customers.age_group
- distinct: 5 | null: 0 (0.000%)
  - `25-34`: 36,342 (29.81%)
  - `35-44`: 31,920 (26.18%)
  - `45-54`: 23,172 (19.00%)
  - `18-24`: 17,039 (13.97%)
  - `55+`: 13,457 (11.04%)

## customers.acquisition_channel
- distinct: 6 | null: 0 (0.000%)
  - `organic_search`: 36,450 (29.89%)
  - `social_media`: 24,448 (20.05%)
  - `paid_search`: 24,285 (19.92%)
  - `email_campaign`: 14,674 (12.03%)
  - `referral`: 12,270 (10.06%)
  - `direct`: 9,803 (8.04%)

## geography.region
- distinct: 3 | null: 0 (0.000%)
  - `East`: 18,929 (47.38%)
  - `Central`: 14,512 (36.33%)
  - `West`: 6,507 (16.29%)

## promotions.promo_type
- distinct: 2 | null: 0 (0.000%)
  - `percentage`: 45 (90.00%)
  - `fixed`: 5 (10.00%)

## promotions.stackable_flag
- distinct: 2 | null: 0 (0.000%)
  - `0`: 38 (76.00%)
  - `1`: 12 (24.00%)

## orders.order_status
- distinct: 6 | null: 0 (0.000%)
  - `delivered`: 516,716 (79.87%)
  - `cancelled`: 59,462 (9.19%)
  - `returned`: 36,142 (5.59%)
  - `shipped`: 13,773 (2.13%)
  - `paid`: 13,577 (2.10%)
  - `created`: 7,275 (1.12%)

## orders.payment_method
- distinct: 5 | null: 0 (0.000%)
  - `credit_card`: 356,352 (55.08%)
  - `paypal`: 97,018 (15.00%)
  - `cod`: 96,681 (14.94%)
  - `apple_pay`: 64,763 (10.01%)
  - `bank_transfer`: 32,131 (4.97%)

## orders.device_type
- distinct: 3 | null: 0 (0.000%)
  - `mobile`: 291,482 (45.06%)
  - `desktop`: 258,855 (40.01%)
  - `tablet`: 96,608 (14.93%)

## orders.order_source
- distinct: 6 | null: 0 (0.000%)
  - `organic_search`: 181,495 (28.05%)
  - `paid_search`: 141,652 (21.90%)
  - `social_media`: 129,710 (20.05%)
  - `email_campaign`: 77,572 (11.99%)
  - `referral`: 64,565 (9.98%)
  - `direct`: 51,951 (8.03%)

## payments.payment_method
- distinct: 5 | null: 0 (0.000%)
  - `credit_card`: 356,352 (55.08%)
  - `paypal`: 97,018 (15.00%)
  - `cod`: 96,681 (14.94%)
  - `apple_pay`: 64,763 (10.01%)
  - `bank_transfer`: 32,131 (4.97%)

## inventory.stockout_flag
- distinct: 2 | null: 0 (0.000%)
  - `1`: 40,571 (67.34%)
  - `0`: 19,676 (32.66%)

## inventory.overstock_flag
- distinct: 2 | null: 0 (0.000%)
  - `1`: 45,942 (76.26%)
  - `0`: 14,305 (23.74%)

## inventory.reorder_flag
- distinct: 1 | null: 0 (0.000%)
  - `0`: 60,247 (100.00%)
- **GHI CHU (@de):** cot chet — 100% = 0, khong bien thien. Nghi hien tuong data (cot du dinh nhung
  chua bao gio bat = 1), khong phai loi parse. KHONG dung lam feature/flag trong model — vo nghia.
  Can @da xac nhan business rule truoc khi loai bo hoan toan.
