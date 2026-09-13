# FinancialState for user-02 (
#     number_of_user=2,
#     user_id=user_02,
#     home_currency=IDR,
#     current_balance=60383889.2,
#     minimum_balance=29158400,
#     financial_priorities=[education, family_support],
#     protected_expenses=[housing, utilities, education],
#     payment_options=[entertainment, cloud_storage, partial_payment, installments],
#         reducible_expenses=[entertainment],
#         stoppable_expenses=[cloud_storage],
#         payment_methods_user_will_consider=[partial_payment, installments],
#     max_installment_months=7,
#     income_events=[event_104, event_112, event_120, event_128, event_136],
#     expense_events=[event_105-event_110, event_113-event_118, event_121-event_126,
#                     event_129-event_134, event_137-event_144, event_145-event_184],
#     pending_events=[event_185],
#     flexible_expenses=[event_110, event_111, event_118, event_119, event_126,
#                        event_127, event_134, event_135, event_142, event_143],
#     relevant_evidence=[
#         message_01: Cobalt Systems increased the monthly salary to IDR 42,750,000
#         starting 2025-08-15; the updated amount appears on the next payslip.
#     ]
# )
#
# Profile row:
# user_02, IDR, current_balance=60383889.2, minimum_balance=29158400,
# priorities=[education, family_support], protected=[housing, utilities, education],
# willing_to_reduce=[entertainment], willing_to_stop=[cloud_storage],
# methods=[partial_payment, installments], max_installment_months=7.
#
# Request linked to user_02:
# request_02:
#     request_date=2025-08-05, type=travel, requested_amount=46018000 IDR,
#     desired_completion_date=2025-10-10, allows_partial_payment=false,
#     text="The current quote for the trip is IDR 46,018,000. I need to
#     complete it by 10 October 2025. Can I afford the full trip without
#     putting upcoming bills at risk?"
#     sample_answer:
#         amount_safe_to_pay=17229139.2,
#         affordability_status=affordable_with_plan,
#         recommended_payment_method=installments,
#         payment_plan=2025-08-08:15952906.67|2025-09-07:15952906.67|
#                      2025-10-07:15952906.67,
#         earliest_date_for_full_payment=2025-09-15,
#         spending_changes_needed=none,
#         explanation="Use 3 installments of IDR 15,952,906.67, starting
#         8 August 2025. This leaves at least IDR 29,158,400 available."
#
# Payment options for request_02:
#     payment_option_05: installments, 3 payments, 15952906.67 each,
#         first=2025-08-08, frequency=30 days, fee=1840720.01,
#         total=47858720.01.
#     payment_option_06: full_payment, 1 payment of 46018000,
#         first=2025-08-05, fee=0, total=46018000.
#     payment_option_07: installments, 18 payments, 2914473.33 each,
#         first=2025-08-12, frequency=31 days, fee=6442519.94,
#         total=52460519.94.
#
# All financial_events for user_02:
#     event_104: income, salary, Payroll credit, credit, 33345000 IDR,
#         event/settled=2025-03-15, flexibility=fixed.
#     event_105: expense, housing, Home repair reserve, debit, 3534000 IDR,
#         event/settled=2025-03-04, flexibility=fixed.
#     event_106: expense, utilities, Municipal utilities, debit, 2143659.02 IDR,
#         event/settled=2025-03-07, flexibility=fixed.
#     event_107: expense, insurance, Household insurance, debit, 1132400 IDR,
#         event/settled=2025-03-08, flexibility=fixed.
#     event_108: expense, education, Course tuition, debit, 3040000 IDR,
#         event/settled=2025-03-09, flexibility=fixed.
#     event_109: expense, healthcare, Clinic payment, debit, 1594883.08 IDR,
#         event/settled=2025-03-11, flexibility=fixed.
#     event_110: expense, entertainment, Cinema and events, debit, 1289187.4 IDR,
#         event/settled=2025-03-15, flexibility=reducible, minimum=670700.
#     event_111: subscription, cloud_storage, Shared storage plan, debit,
#         369550 IDR, event/settled=2025-03-13, flexibility=stoppable.
#     event_112: income, salary, Payroll credit, credit, 33345000 IDR,
#         event/settled=2025-04-15, flexibility=fixed.
#     event_113: expense, housing, Home repair reserve, debit, 3534000 IDR,
#         event/settled=2025-04-04, flexibility=fixed.
#     event_114: expense, utilities, Municipal utilities, debit, 2081730.85 IDR,
#         event/settled=2025-04-07, flexibility=fixed.
#     event_115: expense, insurance, Household insurance, debit, 1132400 IDR,
#         event/settled=2025-04-08, flexibility=fixed.
#     event_116: expense, education, Course tuition, debit, 3040000 IDR,
#         event/settled=2025-04-09, flexibility=fixed.
#     event_117: expense, healthcare, Clinic payment, debit, 1467514.81 IDR,
#         event/settled=2025-04-11, flexibility=fixed.
#     event_118: expense, entertainment, Cinema and events, debit, 1367779.89 IDR,
#         event/settled=2025-04-15, flexibility=reducible, minimum=670700.
#     event_119: subscription, cloud_storage, Shared storage plan, debit,
#         369550 IDR, event/settled=2025-04-13, flexibility=stoppable.
#     event_120: income, salary, Payroll credit, credit, 33345000 IDR,
#         event/settled=2025-05-15, flexibility=fixed.
#     event_121: expense, housing, Home repair reserve, debit, 3534000 IDR,
#         event/settled=2025-05-04, flexibility=fixed.
#     event_122: expense, utilities, Municipal utilities, debit, 1830311.06 IDR,
#         event/settled=2025-05-07, flexibility=fixed.
#     event_123: expense, insurance, Household insurance, debit, 1132400 IDR,
#         event/settled=2025-05-08, flexibility=fixed.
#     event_124: expense, education, Course tuition, debit, 3040000 IDR,
#         event/settled=2025-05-09, flexibility=fixed.
#     event_125: expense, healthcare, Clinic payment, debit, 1452405.16 IDR,
#         event/settled=2025-05-11, flexibility=fixed.
#     event_126: expense, entertainment, Cinema and events, debit, 1287628.28 IDR,
#         event/settled=2025-05-15, flexibility=reducible, minimum=670700.
#     event_127: subscription, cloud_storage, Shared storage plan, debit,
#         369550 IDR, event/settled=2025-05-13, flexibility=stoppable.
#     event_128: income, salary, Payroll credit, credit, 33345000 IDR,
#         event/settled=2025-06-15, flexibility=fixed.
#     event_129: expense, housing, Home repair reserve, debit, 3534000 IDR,
#         event/settled=2025-06-04, flexibility=fixed.
#     event_130: expense, utilities, Municipal utilities, debit, 1981601.61 IDR,
#         event/settled=2025-06-07, flexibility=fixed.
#     event_131: expense, insurance, Household insurance, debit, 1132400 IDR,
#         event/settled=2025-06-08, flexibility=fixed.
#     event_132: expense, education, Course tuition, debit, 3040000 IDR,
#         event/settled=2025-06-09, flexibility=fixed.
#     event_133: expense, healthcare, Clinic payment, debit, 1641668.72 IDR,
#         event/settled=2025-06-11, flexibility=fixed.
#     event_134: expense, entertainment, Cinema and events, debit, 1193699.1 IDR,
#         event/settled=2025-06-15, flexibility=reducible, minimum=670700.
#     event_135: subscription, cloud_storage, Shared storage plan, debit,
#         369550 IDR, event/settled=2025-06-13, flexibility=stoppable.
#     event_136: income, salary, Payroll credit, credit, 33345000 IDR,
#         event/settled=2025-07-15, flexibility=fixed.
#     event_137: expense, housing, Home repair reserve, debit, 3534000 IDR,
#         event/settled=2025-07-04, flexibility=fixed.
#     event_138: expense, utilities, Municipal utilities, debit, 2141849.94 IDR,
#         event/settled=2025-07-07, flexibility=fixed.
#     event_139: expense, insurance, Household insurance, debit, 1132400 IDR,
#         event/settled=2025-07-08, flexibility=fixed.
#     event_140: expense, education, Course tuition, debit, 3040000 IDR,
#         event/settled=2025-07-09, flexibility=fixed.
#     event_141: expense, healthcare, Clinic payment, debit, 1538498.1 IDR,
#         event/settled=2025-07-11, flexibility=fixed.
#     event_142: expense, entertainment, Cinema and events, debit, 1352563.79 IDR,
#         event/settled=2025-07-15, flexibility=reducible, minimum=670700.
#     event_143: subscription, cloud_storage, Shared storage plan, debit,
#         369550 IDR, event/settled=2025-07-13, flexibility=stoppable.
#     event_144: expense, housing, Home repair reserve, debit, 3534000 IDR,
#         event/settled=2025-08-04, flexibility=fixed.
#     event_145: expense, groceries, Grocery delivery, debit, 2477697.53 IDR,
#         event/settled=2025-02-10, flexibility=fixed.
#     event_146: expense, groceries, Bulk pantry shop, debit, 1667911.86 IDR,
#         event/settled=2025-02-20, flexibility=fixed.
#     event_147: expense, groceries, Weekly produce market, debit, 1418745.34 IDR,
#         event/settled=2025-03-02, flexibility=fixed.
#     event_148: expense, groceries, Neighbourhood grocer, debit, 1455258.76 IDR,
#         event/settled=2025-03-12, flexibility=fixed.
#     event_149: expense, groceries, Household groceries, debit, 1920485.7 IDR,
#         event/settled=2025-03-22, flexibility=fixed.
#     event_150: expense, groceries, Household groceries, debit, 1630631.42 IDR,
#         event/settled=2025-04-01, flexibility=fixed.
#     event_151: expense, groceries, Bulk pantry shop, debit, 1664708.05 IDR,
#         event/settled=2025-04-11, flexibility=fixed.
#     event_152: expense, groceries, Household groceries, debit, 1478895.05 IDR,
#         event/settled=2025-04-21, flexibility=fixed.
#     event_153: expense, groceries, Local market purchase, debit, 2192475.45 IDR,
#         event/settled=2025-05-01, flexibility=fixed.
#     event_154: expense, groceries, Supermarket basket, debit, 1852958.27 IDR,
#         event/settled=2025-05-11, flexibility=fixed.
#     event_155: expense, groceries, Neighbourhood grocer, debit, 2030400.43 IDR,
#         event/settled=2025-05-21, flexibility=fixed.
#     event_156: expense, groceries, Local market purchase, debit, 1611886.08 IDR,
#         event/settled=2025-05-31, flexibility=fixed.
#     event_157: expense, groceries, Neighbourhood grocer, debit, 2158165.32 IDR,
#         event/settled=2025-06-10, flexibility=fixed.
#     event_158: expense, groceries, Grocery delivery, debit, 2222527.88 IDR,
#         event/settled=2025-06-20, flexibility=fixed.
#     event_159: expense, groceries, Household groceries, debit, 2079368.25 IDR,
#         event/settled=2025-06-30, flexibility=fixed.
#     event_160: expense, groceries, Local market purchase, debit, 2218141.61 IDR,
#         event/settled=2025-07-10, flexibility=fixed.
#     event_161: expense, groceries, Fresh food shop, debit, 2365919.6 IDR,
#         event/settled=2025-07-20, flexibility=fixed.
#     event_162: expense, groceries, Supermarket basket, debit, 1913686.86 IDR,
#         event/settled=2025-07-30, flexibility=fixed.
#     event_163: expense, transport, Fuel refill, debit, 1373039.34 IDR,
#         event/settled=2025-02-11, flexibility=fixed.
#     event_164: expense, transport, Rail pass, debit, 995704.83 IDR,
#         event/settled=2025-02-25, flexibility=fixed.
#     event_165: expense, transport, Metro and bus fares, debit, 1062246.98 IDR,
#         event/settled=2025-03-11, flexibility=fixed.
#     event_166: expense, transport, Ride-hailing trip, debit, 1053078.61 IDR,
#         event/settled=2025-03-25, flexibility=fixed.
#     event_167: expense, transport, Ride-hailing trip, debit, 1294200.86 IDR,
#         event/settled=2025-04-08, flexibility=fixed.
#     event_168: expense, transport, Ride-hailing trip, debit, 1440242.94 IDR,
#         event/settled=2025-04-22, flexibility=fixed.
#     event_169: expense, transport, Vehicle charging, debit, 1021628.43 IDR,
#         event/settled=2025-05-06, flexibility=fixed.
#     event_170: expense, transport, Commuter pass, debit, 1374936.26 IDR,
#         event/settled=2025-05-20, flexibility=fixed.
#     event_171: expense, transport, Commuter pass, debit, 1329347.44 IDR,
#         event/settled=2025-06-03, flexibility=fixed.
#     event_172: expense, transport, Commuter pass, debit, 1309608.46 IDR,
#         event/settled=2025-06-17, flexibility=fixed.
#     event_173: expense, transport, Rail pass, debit, 1111352.32 IDR,
#         event/settled=2025-07-01, flexibility=fixed.
#     event_174: expense, transport, Commuter pass, debit, 1327886.54 IDR,
#         event/settled=2025-07-15, flexibility=fixed.
#     event_175: expense, transport, Metro and bus fares, debit, 1062310.27 IDR,
#         event/settled=2025-07-29, flexibility=fixed.
#     event_176: expense, dining, Bakery and snacks, debit, 1166644.88 IDR,
#         event/settled=2025-02-12, flexibility=fixed.
#     event_177: expense, dining, Coffee shop, debit, 1101709.76 IDR,
#         event/settled=2025-03-05, flexibility=fixed.
#     event_178: expense, dining, Weekend food delivery, debit, 935929.08 IDR,
#         event/settled=2025-03-26, flexibility=fixed.
#     event_179: expense, dining, Quick-service meal, debit, 1271076.93 IDR,
#         event/settled=2025-04-16, flexibility=fixed.
#     event_180: expense, dining, Takeaway order, debit, 971169.92 IDR,
#         event/settled=2025-05-07, flexibility=fixed.
#     event_181: expense, dining, Neighbourhood restaurant, debit, 1111388.15 IDR,
#         event/settled=2025-05-28, flexibility=fixed.
#     event_182: expense, dining, Bakery and snacks, debit, 947892.35 IDR,
#         event/settled=2025-06-18, flexibility=fixed.
#     event_183: expense, dining, Family dinner, debit, 1043758.65 IDR,
#         event/settled=2025-07-09, flexibility=fixed.
#     event_184: expense, dining, Bakery and snacks, debit, 1204805.34 IDR,
#         event/settled=2025-07-30, flexibility=fixed.
#     event_185: expense, shopping, Pending merchant debit, debit, 1651100 IDR,
#         event_date=2025-08-04, settlement_date=2025-08-08, status=pending,
#         flexibility=fixed.
#
# No images.csv row or linked image exists for user_02. No linked_event_id is
# present in these events, and no exchange-rate conversion is needed because
# all user_02 events and request_02 use IDR.
#-================================================================================================================
#-================================================================================================================
# user_02 decision notes:
#
# 1. Current financial state
#     - Home currency: IDR.
#     - Available balance: IDR 60,383,889.20.
#     - Minimum balance to keep: IDR 29,158,400.
#     - Simple balance above the minimum: IDR 31,225,489.20.
#     - This simple difference is not automatically spendable: upcoming
#       protected expenses, the pending debit, and forecast spending must be
#       reserved first.
#     - Priorities: education and family support.
#     - Protected categories: housing, utilities, and education.
#     - The request is IDR 46,018,000, so full payment today would consume
#       more than the balance available above the required minimum before
#       future obligations are considered.
#
# 2. Future income
#     - message_01 is the relevant payroll evidence. Cobalt Systems confirms
#       the monthly salary increases to IDR 42,750,000 from 2025-08-15.
#     - The updated salary is confirmed payroll evidence and can be counted
#       from its effective/settlement date, not before 2025-08-15.
#     - Do not count unsupported bonuses, commissions, or pending payouts as
#       future income. No image or exchange-rate conversion is needed here.
#
# 3. Future expenses
#     - Forecast the recurring pattern in the historical events over the
#       90-day safety window. The repeated fixed obligations include:
#         housing: Home repair reserve, about IDR 3,534,000 per cycle;
#         utilities: Municipal utilities, about IDR 1.83m-2.14m per cycle;
#         insurance: Household insurance, IDR 1,132,400 per cycle;
#         education: Course tuition, IDR 3,040,000 per cycle;
#         healthcare: Clinic payment, about IDR 1.45m-1.64m per cycle;
#         groceries, transport, and dining: recurring variable spending based
#         on events event_145-event_184.
#     - The protected categories housing, utilities, and education must be
#       included in the forecast. Essential variable spending must also be
#       forecast conservatively rather than ignored.
#
# 4. Pending obligations
#     - event_185 is a pending shopping debit of IDR 1,651,100.
#     - It was recorded on 2025-08-04 and has settlement_date=2025-08-08.
#     - Reserve this debit in the safety calculation; do not treat the
#       pending status as permission to spend the same money again.
#     - No other pending event, linked event, cancellation, or image-based
#       amount is present for user_02.
#
# 5. Flexible expenses we are allowed to change
#     - Entertainment is reducible because the profile allows reducing
#       entertainment. Events event_110, event_118, event_126, event_134,
#       and event_142 show this pattern; each has minimum_allowed_amount=
#       IDR 670,700.
#     - Cloud storage is stoppable because the profile allows stopping
#       cloud_storage. Events event_111, event_119, event_127, event_135,
#       and event_143 are examples, each costing IDR 369,550.
#     - We cannot change housing, utilities, education, insurance, healthcare,
#       groceries, transport, or dining because those events are fixed or the
#       profile does not authorize changing those categories.
#     - A spending change is valid only when it targets a recurring flexible
#       event, respects its minimum amount, and is allowed by the profile.
#
# 6. Payment options
#     - Accepted methods from the profile: partial_payment and installments.
#     - Maximum installment duration: 7 months.
#     - payment_option_05: 3 installments of IDR 15,952,906.67, first payment
#       2025-08-08, every 30 days, financing fee IDR 1,840,720.01, total
#       payable IDR 47,858,720.01. This is eligible and matches the sample
#       recommendation.
#     - payment_option_06: full payment of IDR 46,018,000 on 2025-08-05,
#       fee IDR 0, total IDR 46,018,000. It is not safe against the forecast
#       obligations, and full_payment is not in the user's accepted methods.
#     - payment_option_07: 18 installments of IDR 2,914,473.33, first payment
#       2025-08-12, every 31 days, fee IDR 6,442,519.94, total
#       IDR 52,460,519.94. It exceeds max_installment_months=7 and is not
#       eligible even though installments are generally accepted.
#     - Partial payment is not available for request_02 because
#       allows_partial_payment=false.
#
# 7. What makes an option SAFE?
#     - Every payment in the plan must be affordable on its exact date.
#     - After every payment, protected expense, pending debit, and forecast
#       expense, the balance must remain at least IDR 29,158,400.
#     - Confirmed salary may be counted only from its confirmed settlement
#       date; uncertain income, bonuses, commissions, refunds, and investment
#       gains must not be assumed.
#     - The plan must complete the full IDR 46,018,000 request by
#       2025-10-10 and remain safe throughout the 90-day forecast.
#     - The method must be accepted by the user, fit the maximum installment
#       duration, and exactly match a supplied payment option when using
#       installments.
#     - Applying these checks makes payment_option_05 the safe eligible plan:
#       3 payments finish on 2025-10-07, before the deadline, while the
#       forecast keeps the minimum balance protected. The sample result reports
#       amount_safe_to_pay=IDR 17,229,139.20 and no spending changes needed.

# FinancialState for user-14 (
#     number_of_user=14,
#     user_id=user_14,
#     home_currency=EUR,
#     current_balance=3931.74,
#     minimum_balance=2200,
#     financial_priorities=[healthcare, family_support],
#     protected_expenses=[rent, healthcare, family_support, groceries],
#     payment_options=[shopping, cloud_storage, partial_payment],
#         reducible_expenses=[shopping],
#         stoppable_expenses=[cloud_storage],
#         payment_methods_user_will_consider=[partial_payment],
#     max_installment_months=None,
#     income_events=[event_1162, event_1170, event_1192],
#     expense_events=[event_1163-event_1169, event_1171-event_1177,
#                     event_1178-event_1184, event_1185-event_1191,
#                     event_1193-event_1200, event_1201-event_1239],
#     pending_events=[],
#     flexible_expenses=[event_1168, event_1169, event_1176, event_1177,
#                        event_1183, event_1184, event_1190, event_1191,
#                        event_1198, event_1199],
#     relevant_evidence=[
#         message_10: HarborWorks says the regular salary of EUR 2717 resumes
#         on 2025-08-15, and a recurring childcare payment begins in the same
#         month; updated pay and deductions appear from the next cycle.
#     ]
# )
#
# Profile row:
# user_14, EUR, current_balance=3931.74, minimum_balance=2200,
# priorities=[healthcare, family_support], protected=[rent, healthcare,
# family_support, groceries], willing_to_reduce=[shopping],
# willing_to_stop=[cloud_storage], methods=[partial_payment],
# max_installment_months=blank (no installment limit because installments are
# not an accepted payment method).
#
# Request linked to user_14:
# request_14:
#     request_date=2025-08-04, type=debt_repayment, requested_amount=5414.2 EUR,
#     desired_completion_date=2025-10-04, allows_partial_payment=true,
#     text="I'm planning an extra loan payment of EUR 5,414.20. I need to
#     complete it by 4 October 2025. Would paying this much toward the loan
#     leave enough for the rest of the month?"
#     sample_answer:
#         amount_safe_to_pay=597.74,
#         affordability_status=not_affordable,
#         recommended_payment_method=not_recommended,
#         payment_plan=none,
#         earliest_date_for_full_payment=blank,
#         spending_changes_needed=none,
#         explanation="Do not proceed with the EUR 5,414.20 request. Although
#         EUR 597.74 is available today, the full amount cannot be completed
#         safely within 90 days."
#
# Payment options for request_14:
#     payment_option_39: full_payment, 1 payment of 5414.2,
#         first=2025-08-04, fee=0, total=5414.2.
#     payment_option_40: installments, 18 payments of 342.9,
#         first=2025-08-11, frequency=31 days, fee=758, total=6172.2.
#     The installment option is not eligible because user_14 accepts only
#     partial_payment, not installments.
#
# All financial_events for user_14:
#     event_1162: income, salary, Payroll before leave, credit, 2717 EUR,
#         event/settled=2025-03-15, flexibility=fixed.
#     event_1163: expense, rent, Monthly rent, debit, 688.6 EUR,
#         event/settled=2025-03-03, flexibility=fixed.
#     event_1164: expense, utilities, Energy provider bill, debit, 141.46 EUR,
#         event/settled=2025-03-07, flexibility=fixed.
#     event_1165: debt_payment, debt_repayment, Credit card repayment, debit,
#         350 EUR, event/settled=2025-03-12, flexibility=fixed.
#     event_1166: expense, healthcare, Family healthcare expense, debit, 92.08 EUR,
#         event/settled=2025-03-11, flexibility=fixed.
#     event_1167: expense, family_support, Family support payment, debit, 226 EUR,
#         event/settled=2025-03-14, flexibility=fixed.
#     event_1168: subscription, cloud_storage, Cloud storage plan, debit, 14 EUR,
#         event/settled=2025-03-13, flexibility=stoppable.
#     event_1169: expense, shopping, Online retail purchases, debit, 137.03 EUR,
#         event/settled=2025-03-13, flexibility=reducible, minimum=50.8.
#     event_1170: income, salary, Payroll before leave, credit, 2717 EUR,
#         event/settled=2025-04-15, flexibility=fixed.
#     event_1171: expense, rent, Monthly rent, debit, 688.6 EUR,
#         event/settled=2025-04-03, flexibility=fixed.
#     event_1172: expense, utilities, Energy provider bill, debit, 156.08 EUR,
#         event/settled=2025-04-07, flexibility=fixed.
#     event_1173: debt_payment, debt_repayment, Credit card repayment, debit,
#         350 EUR, event/settled=2025-04-12, flexibility=fixed.
#     event_1174: expense, healthcare, Family healthcare expense, debit, 92.65 EUR,
#         event/settled=2025-04-11, flexibility=fixed.
#     event_1175: expense, family_support, Family support payment, debit, 226 EUR,
#         event/settled=2025-04-14, flexibility=fixed.
#     event_1176: subscription, cloud_storage, Cloud storage plan, debit, 14 EUR,
#         event/settled=2025-04-13, flexibility=stoppable.
#     event_1177: expense, shopping, Online retail purchases, debit, 123.04 EUR,
#         event/settled=2025-04-13, flexibility=reducible, minimum=50.8.
#     event_1178: expense, rent, Monthly rent, debit, 688.6 EUR,
#         event/settled=2025-05-03, flexibility=fixed.
#     event_1179: expense, utilities, Energy provider bill, debit, 143.45 EUR,
#         event/settled=2025-05-07, flexibility=fixed.
#     event_1180: debt_payment, debt_repayment, Credit card repayment, debit,
#         350 EUR, event/settled=2025-05-12, flexibility=fixed.
#     event_1181: expense, healthcare, Family healthcare expense, debit, 95.17 EUR,
#         event/settled=2025-05-11, flexibility=fixed.
#     event_1182: expense, family_support, Family support payment, debit, 226 EUR,
#         event/settled=2025-05-14, flexibility=fixed.
#     event_1183: subscription, cloud_storage, Cloud storage plan, debit, 14 EUR,
#         event/settled=2025-05-13, flexibility=stoppable.
#     event_1184: expense, shopping, Online retail purchases, debit, 123.12 EUR,
#         event/settled=2025-05-13, flexibility=reducible, minimum=50.8.
#     event_1185: expense, rent, Monthly rent, debit, 688.6 EUR,
#         event/settled=2025-06-03, flexibility=fixed.
#     event_1186: expense, utilities, Energy provider bill, debit, 146.41 EUR,
#         event/settled=2025-06-07, flexibility=fixed.
#     event_1187: debt_payment, debt_repayment, Credit card repayment, debit,
#         350 EUR, event/settled=2025-06-12, flexibility=fixed.
#     event_1188: expense, healthcare, Family healthcare expense, debit, 91.77 EUR,
#         event/settled=2025-06-11, flexibility=fixed.
#     event_1189: expense, family_support, Family support payment, debit, 226 EUR,
#         event/settled=2025-06-14, flexibility=fixed.
#     event_1190: subscription, cloud_storage, Cloud storage plan, debit, 14 EUR,
#         event/settled=2025-06-13, flexibility=stoppable.
#     event_1191: expense, shopping, Online retail purchases, debit, 123.77 EUR,
#         event/settled=2025-06-13, flexibility=reducible, minimum=50.8.
#     event_1192: income, salary, Payroll after returning from leave, credit,
#         2717 EUR, event/settled=2025-07-15, flexibility=fixed.
#     event_1193: expense, rent, Monthly rent, debit, 688.6 EUR,
#         event/settled=2025-07-03, flexibility=fixed.
#     event_1194: expense, utilities, Energy provider bill, debit, 153.69 EUR,
#         event/settled=2025-07-07, flexibility=fixed.
#     event_1195: debt_payment, debt_repayment, Credit card repayment, debit,
#         350 EUR, event/settled=2025-07-12, flexibility=fixed.
#     event_1196: expense, healthcare, Family healthcare expense, debit, 87.84 EUR,
#         event/settled=2025-07-11, flexibility=fixed.
#     event_1197: expense, family_support, Family support payment, debit, 226 EUR,
#         event/settled=2025-07-14, flexibility=fixed.
#     event_1198: subscription, cloud_storage, Cloud storage plan, debit, 14 EUR,
#         event/settled=2025-07-13, flexibility=stoppable.
#     event_1199: expense, shopping, Online retail purchases, debit, 140.39 EUR,
#         event/settled=2025-07-13, flexibility=reducible, minimum=50.8.
#     event_1200: expense, rent, Monthly rent, debit, 688.6 EUR,
#         event/settled=2025-08-03, flexibility=fixed.
#     event_1201: expense, groceries, Weekly produce market, debit, 103.53 EUR,
#         event/settled=2025-02-09, flexibility=fixed.
#     event_1202: expense, groceries, Local market purchase, debit, 95.35 EUR,
#         event/settled=2025-02-16, flexibility=fixed.
#     event_1203: expense, groceries, Grocery delivery, debit, 104.91 EUR,
#         event/settled=2025-02-23, flexibility=fixed.
#     event_1204: expense, groceries, Fresh food shop, debit, 81.22 EUR,
#         event/settled=2025-03-02, flexibility=fixed.
#     event_1205: expense, groceries, Grocery delivery, debit, 92.09 EUR,
#         event/settled=2025-03-09, flexibility=fixed.
#     event_1206: expense, groceries, Household groceries, debit, 121.61 EUR,
#         event/settled=2025-03-16, flexibility=fixed.
#     event_1207: expense, groceries, Bulk pantry shop, debit, 87.64 EUR,
#         event/settled=2025-03-23, flexibility=fixed.
#     event_1208: expense, groceries, Household groceries, debit, 140.51 EUR,
#         event/settled=2025-03-30, flexibility=fixed.
#     event_1209: expense, groceries, Fresh food shop, debit, 131.02 EUR,
#         event/settled=2025-04-06, flexibility=fixed.
#     event_1210: expense, groceries, Local market purchase, debit, 83.71 EUR,
#         event/settled=2025-04-13, flexibility=fixed.
#     event_1211: expense, groceries, Grocery delivery, debit, 93.46 EUR,
#         event/settled=2025-04-20, flexibility=fixed.
#     event_1212: expense, groceries, Grocery delivery, debit, 90.76 EUR,
#         event/settled=2025-04-27, flexibility=fixed.
#     event_1213: expense, groceries, Supermarket basket, debit, 106.55 EUR,
#         event/settled=2025-05-04, flexibility=fixed.
#     event_1214: expense, groceries, Neighbourhood grocer, debit, 93.65 EUR,
#         event/settled=2025-05-11, flexibility=fixed.
#     event_1215: expense, groceries, Supermarket basket, debit, 96.42 EUR,
#         event/settled=2025-05-18, flexibility=fixed.
#     event_1216: expense, groceries, Supermarket basket, debit, 101.15 EUR,
#         event/settled=2025-05-25, flexibility=fixed.
#     event_1217: expense, groceries, Fresh food shop, debit, 129.68 EUR,
#         event/settled=2025-06-01, flexibility=fixed.
#     event_1218: expense, groceries, Grocery delivery, debit, 123.41 EUR,
#         event/settled=2025-06-08, flexibility=fixed.
#     event_1219: expense, groceries, Bulk pantry shop, debit, 94.21 EUR,
#         event/settled=2025-06-15, flexibility=fixed.
#     event_1220: expense, groceries, Neighbourhood grocer, debit, 86.49 EUR,
#         event/settled=2025-06-22, flexibility=fixed.
#     event_1221: expense, groceries, Weekly produce market, debit, 138.85 EUR,
#         event/settled=2025-06-29, flexibility=fixed.
#     event_1222: expense, groceries, Local market purchase, debit, 102.54 EUR,
#         event/settled=2025-07-06, flexibility=fixed.
#     event_1223: expense, groceries, Weekly produce market, debit, 112.72 EUR,
#         event/settled=2025-07-13, flexibility=fixed.
#     event_1224: expense, groceries, Local market purchase, debit, 96.86 EUR,
#         event/settled=2025-07-20, flexibility=fixed.
#     event_1225: expense, groceries, Weekly produce market, debit, 86.83 EUR,
#         event/settled=2025-07-27, flexibility=fixed.
#     event_1226: expense, groceries, Bulk pantry shop, debit, 129.56 EUR,
#         event/settled=2025-08-03, flexibility=fixed.
#     event_1227: expense, transport, Vehicle charging, debit, 46.75 EUR,
#         event/settled=2025-02-10, flexibility=fixed.
#     event_1228: expense, transport, Vehicle charging, debit, 58.52 EUR,
#         event/settled=2025-02-24, flexibility=fixed.
#     event_1229: expense, transport, Parking and tolls, debit, 37.65 EUR,
#         event/settled=2025-03-10, flexibility=fixed.
#     event_1230: expense, transport, Metro and bus fares, debit, 47.73 EUR,
#         event/settled=2025-03-24, flexibility=fixed.
#     event_1231: expense, transport, Local taxi, debit, 53.15 EUR,
#         event/settled=2025-04-07, flexibility=fixed.
#     event_1232: expense, transport, Fuel refill, debit, 56.49 EUR,
#         event/settled=2025-04-21, flexibility=fixed.
#     event_1233: expense, transport, Fuel refill, debit, 55.52 EUR,
#         event/settled=2025-05-05, flexibility=fixed.
#     event_1234: expense, transport, Ride-hailing trip, debit, 52.26 EUR,
#         event/settled=2025-05-19, flexibility=fixed.
#     event_1235: expense, transport, Parking and tolls, debit, 50.48 EUR,
#         event/settled=2025-06-02, flexibility=fixed.
#     event_1236: expense, transport, Commuter pass, debit, 55.96 EUR,
#         event/settled=2025-06-16, flexibility=fixed.
#     event_1237: expense, transport, Rail pass, debit, 62.3 EUR,
#         event/settled=2025-06-30, flexibility=fixed.
#     event_1238: expense, transport, Rail pass, debit, 43.12 EUR,
#         event/settled=2025-07-14, flexibility=fixed.
#     event_1239: expense, transport, Ride-hailing trip, debit, 43.88 EUR,
#         event/settled=2025-07-28, flexibility=fixed.
#
# No images.csv row, related_event_id, or linked event exists for user_14.
# No exchange-rate conversion is needed because all user_14 data uses EUR.