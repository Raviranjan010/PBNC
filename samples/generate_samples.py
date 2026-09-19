import os
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont

def generate_samples(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    # 1. Clean Digital Multi-page Exam
    doc1 = fitz.open()
    # Page 1
    p1 = doc1.new_page()
    text_p1 = (
        "PAPERMIND COMPREHENSIVE EXAMINATION - COMPUTER SCIENCE\n"
        "Time Allowed: 3 Hours                                  Maximum Marks: 100\n"
        "---------------------------------------------------------------------------\n\n"
        "1. What is the primary purpose of Database Normalization?\n"
        "   (A) To eliminate redundant data and avoid update anomalies\n"
        "   (B) To maximize storage usage on hard drives\n"
        "   (C) To increase SQL query parsing latency\n"
        "   (D) To automatically encrypt all stored data\n\n"
        "2. Which data structure operates under the Last-In, First-Out (LIFO) principle?\n"
        "   (A) Queue\n"
        "   (B) Stack\n"
        "   (C) Binary Search Tree\n"
        "   (D) Hash Map\n\n"
    )
    p1.insert_text((50, 72), text_p1, fontsize=12)
    
    # Page 2
    p2 = doc1.new_page()
    text_p2 = (
        "3. What is the time complexity of searching an element in a balanced Binary Search Tree?\n"
        "   (A) O(1)\n"
        "   (B) O(n)\n"
        "   (C) O(log n)\n"
        "   (D) O(n log n)\n\n"
        "4. In Python, which keyword is used to create an anonymous function?\n"
        "   (A) def\n"
        "   (B) lambda\n"
        "   (C) func\n"
        "   (D) anonymous\n\n"
    )
    p2.insert_text((50, 72), text_p2, fontsize=12)
    doc1.save(os.path.join(output_dir, "sample_digital_exam.pdf"))
    doc1.close()

    # 2. Multi-Page Question Exam (Question 2 starts on Page 1, options on Page 2)
    doc2 = fitz.open()
    mp_p1 = doc2.new_page()
    mp_text_p1 = (
        "PAPERMIND CROSS-PAGE DEMO EXAM\n"
        "Section A: Operating Systems\n"
        "---------------------------------------------------------------------------\n\n"
        "1. Which component of an OS is loaded into memory first during boot?\n"
        "   (A) Shell\n"
        "   (B) Kernel\n"
        "   (C) Desktop GUI\n"
        "   (D) Web Browser\n\n"
        "2. In modern multi-threaded operating systems, describe how synchronization is achieved between concurrent processes attempting to access shared critical sections of memory:\n"
    )
    mp_p1.insert_text((50, 72), mp_text_p1, fontsize=12)

    mp_p2 = doc2.new_page()
    mp_text_p2 = (
        "   (A) Mutex locks and counting semaphores\n"
        "   (B) Infinite spin loops with no yield\n"
        "   (C) Random process termination\n"
        "   (D) Disabling all hardware interrupts permanently\n\n"
        "3. Which scheduling algorithm may lead to starvation of low-priority tasks?\n"
        "   (A) Round Robin\n"
        "   (B) First-Come First-Served\n"
        "   (C) Strict Priority Scheduling\n"
        "   (D) Fair Share Scheduling\n\n"
    )
    mp_p2.insert_text((50, 72), mp_text_p2, fontsize=12)
    doc2.save(os.path.join(output_dir, "sample_multipage_question.pdf"))
    doc2.close()

    # 3. Exam With Embedded Answer Key
    doc3 = fitz.open()
    ak_p1 = doc3.new_page()
    ak_text_p1 = (
        "PAPERMIND TEST PAPER WITH INLINE KEY\n"
        "---------------------------------------------------------------------------\n\n"
        "1. What does ACID stand for in database management systems?\n"
        "   (A) Atomicity, Consistency, Isolation, Durability\n"
        "   (B) Access, Control, Indexing, Direct\n"
        "   (C) Asynchronous, Concurrent, Integrated, Distributed\n"
        "   (D) Automated, Coordinated, Isolated, Distributed\n\n"
        "2. What protocol is used to securely transfer hypertext web pages?\n"
        "   (A) FTP\n"
        "   (B) SMTP\n"
        "   (C) HTTPS\n"
        "   (D) Telnet\n\n"
        "---------------------------------------------------------------------------\n"
        "Answer Key:\n"
        "1. A\n"
        "2. C\n"
    )
    ak_p1.insert_text((50, 72), ak_text_p1, fontsize=12)
    doc3.save(os.path.join(output_dir, "sample_exam_with_key.pdf"))
    doc3.close()

    # 4. Standalone Separate Answer Key Document
    doc4 = fitz.open()
    sep_p1 = doc4.new_page()
    sep_text = (
        "OFFICIAL ANSWER KEY DOCUMENT\n"
        "Subject: Computer Science Examination\n"
        "Document Reference: sample_digital_exam\n"
        "---------------------------------------------------------------------------\n\n"
        "Solutions:\n"
        "1. A\n"
        "2. B\n"
        "3. C\n"
        "4. B\n"
    )
    sep_p1.insert_text((50, 72), sep_text, fontsize=12)
    doc4.save(os.path.join(output_dir, "sample_separate_answer_key.pdf"))
    doc4.close()

    # 5. Image Question Paper (PNG)
    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((40, 40), "PAPERMIND IMAGE EXAM (PNG SAMPLE)", fill=(0, 0, 0))
    draw.text((40, 70), "------------------------------------------------------------", fill=(50, 50, 50))
    draw.text((40, 110), "1. What is the hexadecimal representation of decimal 255?", fill=(0, 0, 0))
    draw.text((60, 140), "(A) FF", fill=(0, 0, 0))
    draw.text((60, 170), "(B) 100", fill=(0, 0, 0))
    draw.text((60, 200), "(C) 0F", fill=(0, 0, 0))
    draw.text((60, 230), "(D) AA", fill=(0, 0, 0))
    draw.text((40, 280), "2. Which layer in OSI model handles physical addressing (MAC)?", fill=(0, 0, 0))
    draw.text((60, 310), "(A) Network Layer", fill=(0, 0, 0))
    draw.text((60, 340), "(B) Data Link Layer", fill=(0, 0, 0))
    draw.text((60, 370), "(C) Transport Layer", fill=(0, 0, 0))
    draw.text((60, 400), "(D) Application Layer", fill=(0, 0, 0))
    img.save(os.path.join(output_dir, "sample_scanned_exam.png"))

    # 6. Low Quality / Degraded Scan (simulated low contrast and noise)
    low_img = Image.new("RGB", (600, 400), color=(180, 180, 180))
    draw_low = ImageDraw.Draw(low_img)
    draw_low.text((30, 30), "Low contrast degraded scan specimen", fill=(160, 160, 160))
    draw_low.text((30, 70), "1. Q??? What is... [degraded text]", fill=(155, 155, 155))
    low_img.save(os.path.join(output_dir, "sample_low_quality_scan.png"))

    # 7. Malformed / Corrupt Document
    with open(os.path.join(output_dir, "sample_malformed.pdf"), "wb") as f:
        f.write(b"NOT A REAL PDF FILE CONTENT RANDOM CORRUPTION 12345")

    print("Sample test fixtures successfully generated in:", output_dir)

if __name__ == "__main__":
    generate_samples("samples")
