#!/usr/bin/env python3
"""
Tách vlog thành 3 phần để render riêng rồi ghép lại.
Part 1: 0-30s  | Part 2: 30-60s | Part 3: 60-80s
"""
import re

CSS = open("index.html").read().split("<style>")[1].split("</style>")[0]

def make_html(part_id, offset, duration, clips_html, audio_html, captions_html, body_html, timeline_js):
    return f"""<!doctype html>
<html lang="vi">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>{CSS}</style>
  </head>
  <body>
    <div id="root"
      data-composition-id="{part_id}"
      data-start="0"
      data-duration="{duration}"
      data-width="1080"
      data-height="1920"
    >
{clips_html}
      <!-- ── Bottom gradient ── -->
      <div id="bot-grad"></div>
{audio_html}
      <!-- ── Caption layer ── -->
      <div id="cap-layer">
{captions_html}
      </div>
{body_html}
    </div>

    <script>
      /* zoomCut disabled for render */
      function zoomCut(t) {{}}

      function showCap(id, t, dur) {{
        tl.fromTo(`#${{id}}`,
          {{ opacity: 0, y: 18 }},
          {{ opacity: 1, y: 0, duration: 0.4, ease: "power2.out" }},
          t);
        if (dur) {{
          tl.to(`#${{id}}`, {{ opacity: 0, y: -8, duration: 0.25, ease: "power2.in" }}, t + dur);
        }}
      }}

      const tl = gsap.timeline({{ paused: true }});

{timeline_js}

      window.__timelines = window.__timelines || {{}};
      window.__timelines["{part_id}"] = tl;
    </script>
  </body>
</html>
"""

# ── PART 1: 0-30s ──────────────────────────────────────────────

P1_CLIPS = """      <video id="c01" class="bg-vid clip" src="assets/c01.mp4"
        muted preload="auto" playsinline
        data-start="0" data-duration="11" data-track-index="1" data-volume="0"></video>
      <video id="c02" class="bg-vid clip" src="assets/c02.mp4"
        muted preload="auto" playsinline
        data-start="11" data-duration="5" data-track-index="2" data-volume="0"></video>
      <video id="c03" class="bg-vid clip" src="assets/c03.mp4"
        muted preload="auto" playsinline
        data-start="16" data-duration="5" data-track-index="3" data-volume="0"></video>
      <video id="c04" class="bg-vid clip" src="assets/c04.mp4"
        muted preload="auto" playsinline
        data-start="20" data-duration="10" data-track-index="4" data-volume="0"></video>"""

P1_AUDIO = """      <audio id="bgm" class="clip" src="assets/bgm.mp3" preload="auto"
        data-start="0" data-duration="30" data-track-index="0" data-volume="0.2"></audio>
      <audio id="vo0" class="clip" src="assets/vo_s0.mp3" preload="auto"
        data-start="0.3" data-duration="6" data-track-index="20" data-volume="1"></audio>
      <audio id="vo1" class="clip" src="assets/vo_s1.mp3" preload="auto"
        data-start="11.2" data-duration="6" data-track-index="21" data-volume="1"></audio>
      <audio id="vo2" class="clip" src="assets/vo_s2.mp3" preload="auto"
        data-start="20.2" data-duration="7" data-track-index="22" data-volume="1"></audio>
      <audio id="sfx-hook-w" class="clip" src="assets/sfx_whoosh.mp3" preload="auto"
        data-start="0" data-duration="2" data-track-index="30" data-volume="0.5"></audio>
      <audio id="sfx-hook-p" class="clip" src="assets/sfx_pop.mp3" preload="auto"
        data-start="0.35" data-duration="1" data-track-index="31" data-volume="0.4"></audio>"""

P1_CAPTIONS = """        <!-- S0 Hook -->
        <div id="c-s0-1" class="cap cap-hook">Sale chưa có khách<br />thì làm gì?</div>
        <div id="c-s0-2" class="cap cap-hook-sub">Bình dẫn bạn vào xem sự kiện Sun Group.</div>
        <div id="c-s0-3" class="cap cap-hook-cue">Bình Phan · IQI Đà Nẵng</div>
        <!-- S1 -->
        <div id="c-s1-1" class="cap cap-body">Không phải sự kiện<br>ra mắt thông thường.</div>
        <div id="c-s1-2" class="cap cap-body">Đây là lễ bàn giao<br>sổ đỏ thật sự.</div>
        <div id="c-s1-3" class="cap cap-body">Cư dân nhận giấy tờ,<br>chụp ảnh, bắt tay.</div>
        <!-- S2 -->
        <div id="c-s2-1" class="cap cap-body">Mình để ý kỹ hơn.</div>
        <div id="c-s2-2" class="cap cap-body">Khách hôm nay<br>không chủ yếu từ Đà Nẵng.</div>
        <div id="c-s2-3" class="cap cap-body">Hà Nội, Sài Gòn<br>chiếm gần một nửa.<br>Tín hiệu cần để ý.</div>"""

P1_BODY = """      <div id="brand-badge">Bình Phan <span>IQI</span></div>"""

P1_TIMELINE = """      // Video clips
      tl.fromTo("#c01", {opacity:0}, {opacity:1, duration:0.4}, 0);
      tl.to("#c01", {opacity:0, duration:0.3}, 10.7);
      tl.fromTo("#c02", {opacity:0}, {opacity:1, duration:0.3}, 11);
      tl.to("#c02", {opacity:0, duration:0.3}, 15.7);
      tl.fromTo("#c03", {opacity:0}, {opacity:1, duration:0.3}, 16);
      tl.to("#c03", {opacity:0, duration:0.3}, 19.7);
      tl.fromTo("#c04", {opacity:0}, {opacity:1, duration:0.3}, 20);
      tl.to("#c04", {opacity:0, duration:0.3}, 29.7);

      // Brand badge
      tl.fromTo("#brand-badge", {opacity:0, y:8}, {opacity:1, y:0, duration:0.5, ease:"power2.out"}, 0.4);
      tl.to("#brand-badge", {opacity:0, duration:0.4}, 4.5);

      // S0 captions
      showCap("c-s0-1", 0.3, 1.3);
      showCap("c-s0-2", 1.9, 2.1);
      showCap("c-s0-3", 4.5, 4.0);

      // S1
      zoomCut(11);
      showCap("c-s1-1", 11.3, 1.5);
      showCap("c-s1-2", 12.9, 1.8);
      showCap("c-s1-3", 14.9, 4.0);

      // S2
      zoomCut(20);
      showCap("c-s2-1", 20.3, 0.9);
      showCap("c-s2-2", 21.5, 1.9);
      showCap("c-s2-3", 23.3, 5.5);"""

# ── PART 2: 30-60s → offset -30 ─────────────────────────────────

P2_CLIPS = """      <video id="c05" class="bg-vid clip" src="assets/c05.mp4"
        muted preload="auto" playsinline
        data-start="0" data-duration="7" data-track-index="1" data-volume="0"></video>
      <video id="c06" class="bg-vid clip" src="assets/c06.mp4"
        muted preload="auto" playsinline
        data-start="7" data-duration="5" data-track-index="2" data-volume="0"></video>
      <video id="c07" class="bg-vid clip" src="assets/c07.mp4"
        muted preload="auto" playsinline
        data-start="12" data-duration="8" data-track-index="3" data-volume="0"></video>
      <video id="c08" class="bg-vid clip" src="assets/c08.mp4"
        muted preload="auto" playsinline
        data-start="20" data-duration="10" data-track-index="4" data-volume="0"></video>"""

P2_AUDIO = """      <audio id="bgm" class="clip" src="assets/bgm.mp3" preload="auto"
        data-start="0" data-duration="30" data-track-index="0" data-volume="0.2"></audio>
      <audio id="vo3" class="clip" src="assets/vo_s3.mp3" preload="auto"
        data-start="0.2" data-duration="11" data-track-index="23" data-volume="1"></audio>
      <audio id="vo4" class="clip" src="assets/vo_s4.mp3" preload="auto"
        data-start="12.2" data-duration="6" data-track-index="24" data-volume="1"></audio>
      <audio id="vo5" class="clip" src="assets/vo_s5.mp3" preload="auto"
        data-start="20.2" data-duration="8" data-track-index="25" data-volume="1"></audio>"""

P2_CAPTIONS = """        <!-- S3 (offset -30) -->
        <div id="c-s3-1" class="cap cap-body">Sa bàn tổ hợp Symphony.</div>
        <div id="c-s3-2" class="cap cap-body">Bốn tháp:<br>1, 2, 3 và 5.</div>
        <div id="c-s3-3" class="cap cap-body">1, 2, 3 vừa bàn giao.</div>
        <div id="c-s3-4" class="cap cap-body">Symphony 5<br>đang mở bán.</div>
        <div id="c-s3-5" class="cap cap-body">Cùng 1 sự kiện, 2 câu chuyện.</div>
        <!-- S4 (offset -30) -->
        <div id="c-s4-1" class="cap cap-body">Mình nhận ra:</div>
        <div id="c-s4-2" class="cap cap-body">Khách đứng ở sa bàn<br>lâu hơn nghe thuyết trình.</div>
        <div id="c-s4-3" class="cap cap-body">Người ta mua bằng hình ảnh.<br>Không phải con số.</div>
        <!-- S5 (offset -30) -->
        <div id="c-s5-1" class="cap cap-body">Cái mình thích nhất<br>ở sự kiện như vầy:</div>
        <div id="c-s5-2" class="cap cap-body">Cuộc trò chuyện<br>không có trong kịch bản.</div>
        <div id="c-s5-3" class="cap cap-body">Đó là lúc học được<br>nhiều nhất.</div>"""

P2_BODY = ""

P2_TIMELINE = """      // Video clips (offset -30)
      tl.fromTo("#c05", {opacity:0}, {opacity:1, duration:0.3}, 0);
      tl.to("#c05", {opacity:0, duration:0.3}, 6.7);
      tl.fromTo("#c06", {opacity:0}, {opacity:1, duration:0.3}, 7);
      tl.to("#c06", {opacity:0, duration:0.3}, 11.7);
      tl.fromTo("#c07", {opacity:0}, {opacity:1, duration:0.3}, 12);
      tl.to("#c07", {opacity:0, duration:0.3}, 19.7);
      tl.fromTo("#c08", {opacity:0}, {opacity:1, duration:0.3}, 20);
      tl.to("#c08", {opacity:0, duration:0.3}, 29.7);

      // S3 captions (offset -30)
      zoomCut(0);
      showCap("c-s3-1", 0.3,  1.8);
      showCap("c-s3-2", 2.4,  2.3);
      showCap("c-s3-3", 5.1,  1.5);
      showCap("c-s3-4", 7.0,  1.1);
      showCap("c-s3-5", 8.4,  3.3);

      // S4 captions (offset -30)
      zoomCut(12);
      showCap("c-s4-1", 12.3, 0.5);
      showCap("c-s4-2", 12.9, 2.2);
      showCap("c-s4-3", 15.2, 4.0);

      // S5 captions (offset -30)
      zoomCut(20);
      showCap("c-s5-1", 20.3, 2.0);
      showCap("c-s5-2", 22.5, 1.8);
      showCap("c-s5-3", 26.2, 3.0);"""

# ── PART 3: 60-80s → offset -60 ─────────────────────────────────

P3_CLIPS = """      <video id="c04b" class="bg-vid clip" src="assets/c04b.mp4"
        muted preload="auto" playsinline
        data-start="0" data-duration="7" data-track-index="1" data-volume="0"></video>
      <video id="c07b" class="bg-vid clip" src="assets/c07b.mp4"
        muted preload="auto" playsinline
        data-start="7" data-duration="7" data-track-index="2" data-volume="0"></video>
      <video id="c06b" class="bg-vid clip" src="assets/c06b.mp4"
        muted preload="auto" playsinline
        data-start="14" data-duration="6" data-track-index="3" data-volume="0"></video>"""

P3_AUDIO = """      <audio id="bgm" class="clip" src="assets/bgm.mp3" preload="auto"
        data-start="0" data-duration="20" data-track-index="0" data-volume="0.2"></audio>
      <audio id="vo6" class="clip" src="assets/vo_s6.mp3" preload="auto"
        data-start="0.2" data-duration="12" data-track-index="26" data-volume="1"></audio>
      <audio id="vo7" class="clip" src="assets/vo_s7.mp3" preload="auto"
        data-start="14.2" data-duration="3" data-track-index="27" data-volume="1"></audio>
      <audio id="sfx-cta-p" class="clip" src="assets/sfx_pop.mp3" preload="auto"
        data-start="14" data-duration="1" data-track-index="32" data-volume="0.4"></audio>
      <audio id="sfx-cta-w" class="clip" src="assets/sfx_whoosh.mp3" preload="auto"
        data-start="14.3" data-duration="2" data-track-index="33" data-volume="0.3"></audio>"""

P3_CAPTIONS = """        <!-- S6 (offset -60) -->
        <div id="c-s6-1" class="cap cap-body">Mình qua nhiều<br>sự kiện rồi.</div>
        <div id="c-s6-2" class="cap cap-body">Nhưng lễ bàn giao sổ đỏ<br>thật sự khác.</div>
        <div id="c-s6-3" class="cap cap-body">Cư dân cầm tờ giấy đó,<br>mặt họ khác.</div>
        <div id="c-s6-4" class="cap cap-body">Không phải vì<br>giá trị tài sản.</div>
        <div id="c-s6-5" class="cap cap-body">Mà vì lời hứa được giữ.</div>
        <div id="c-s6-6" class="cap cap-body">Hôm nay có một khách<br>hỏi Bình một câu...</div>
        <div id="c-s6-7" class="cap cap-body">Video sau mình kể.</div>"""

P3_BODY = """      <!-- CTA -->
      <div id="cta">
        <img id="cta-avatar" class="cta-avatar clip" src="assets/me-outtro.jpg" alt=""
          data-start="14" data-duration="6" data-track-index="50" data-volume="0" />
        <div id="cta-main" class="cta-main clip"
          data-start="14" data-duration="6" data-track-index="51" data-volume="0"
          style="opacity:0">Theo dõi Bình</div>
        <div id="cta-sub" class="cta-sub clip"
          data-start="14" data-duration="6" data-track-index="52" data-volume="0"
          style="opacity:0">để xem thêm hậu trường<br />như vầy nhé.</div>
        <div id="cta-name" class="cta-name clip"
          data-start="14" data-duration="6" data-track-index="53" data-volume="0"
          style="opacity:0">Bình Phan <span>IQI</span></div>
      </div>"""

P3_TIMELINE = """      // Video clips (offset -60)
      tl.fromTo("#c04b", {opacity:0}, {opacity:1, duration:0.3}, 0);
      tl.to("#c04b", {opacity:0, duration:0.3}, 6.7);
      tl.fromTo("#c07b", {opacity:0}, {opacity:1, duration:0.3}, 7);
      tl.to("#c07b", {opacity:0, duration:0.3}, 13.7);
      tl.fromTo("#c06b", {opacity:0}, {opacity:1, duration:0.5}, 14);

      // S6 captions (offset -60)
      zoomCut(0);
      showCap("c-s6-1", 0.3,  1.0);
      showCap("c-s6-2", 1.7,  1.3);
      showCap("c-s6-3", 3.6,  1.6);
      showCap("c-s6-4", 5.7,  1.3);
      showCap("c-s6-5", 7.2,  1.7);
      showCap("c-s6-6", 8.7,  1.7);
      showCap("c-s6-7", 10.8, 3.0);

      // S7 CTA (offset -60)
      zoomCut(14);
      tl.fromTo("#cta",      {opacity:0}, {opacity:1, duration:0.6, ease:"power2.out"}, 14);
      tl.fromTo("#cta-avatar", {opacity:0, scale:0.88}, {opacity:1, scale:1, duration:0.6, ease:"back.out(1.4)"}, 14.2);
      tl.fromTo("#cta-main",   {opacity:0, y:24}, {opacity:1, y:0, duration:0.5, ease:"power3.out"}, 14.5);
      tl.fromTo("#cta-sub",    {opacity:0, y:16}, {opacity:1, y:0, duration:0.5, ease:"power3.out"}, 14.85);
      tl.fromTo("#cta-name",   {opacity:0, y:10}, {opacity:1, y:0, duration:0.4, ease:"power2.out"}, 15.2);"""

# Write 3 files
files = [
    ("part1.html", "vlog-part1", 0, 30, P1_CLIPS, P1_AUDIO, P1_CAPTIONS, P1_BODY, P1_TIMELINE),
    ("part2.html", "vlog-part2", 30, 30, P2_CLIPS, P2_AUDIO, P2_CAPTIONS, P2_BODY, P2_TIMELINE),
    ("part3.html", "vlog-part3", 60, 20, P3_CLIPS, P3_AUDIO, P3_CAPTIONS, P3_BODY, P3_TIMELINE),
]

for fname, pid, offset, duration, clips, audio, captions, body, timeline in files:
    html = make_html(pid, offset, duration, clips, audio, captions, body, timeline)
    with open(fname, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Created {fname} ({duration}s, offset -{offset}s)")

print("Done — render 3 files rồi concat với ffmpeg")
