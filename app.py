import streamlit as st
import pandas as pd
import io
from datetime import datetime

# --- 1. دالة معالجة البيانات وتحويلها لـ Excel ---
def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='تقرير_الأداء_اليومي')
        # يمكن إضافة تنسيقات احترافية هنا لاحقاً
    return output.getvalue()

# --- 2. إضافة واجهة التقارير داخل التبويب الثاني (📊) ---
with tab2:
    st.markdown("---")
    st.subheader("📁 مركز تصدير البيانات")
    
    col_a, col_b = st.columns([2, 1])
    
    with col_a:
        st.write("يمكنك الآن استخراج سجل الصفقات الكامل وتحميله بصيغة Excel لمراجعته يدوياً أو مشاركته.")
        
    with col_b:
        # تجهيز البيانات للتحميل
        if not log_df.empty:
            excel_data = convert_df_to_excel(log_df)
            
            # زر التحميل اليدوي
            st.download_button(
                label="📥 تحميل تقرير الإكسل",
                data=excel_data,
                file_name=f"Trading_Report_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="اضغط هنا للحصول على ملف Excel يحتوي على كافة تفاصيل صفقات اليوم"
            )
        else:
            st.warning("لا توجد بيانات مسجلة للتصدير حالياً.")

    # --- زر إرسال الملخص للتليجرام يدوياً ---
    if st.button("📤 إرسال ملخص الأداء إلى Telegram الآن"):
        if not log_df.empty:
            # استدعاء دالة الإرسال التي برمجناها سابقاً
            send_closing_summary(log_df)
            st.success("تم إرسال التقرير بنجاح إلى هاتفك! ✅")
        else:
            st.error("السجل فارغ، لا توجد بيانات لإرسالها.")
