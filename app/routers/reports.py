from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from io import BytesIO, StringIO
import csv

from app.database import get_db
from app.models.user import User
from app.models.stats import UserStats
from app.models.food_log import FoodLog
from app.models.food import Food
from app.models.workout import WorkoutSession, WorkoutSet, WorkoutExercise
from app.core.dependencies import get_current_user
from app.routers.summary import compute_daily

router = APIRouter(prefix="/reports", tags=["Reports"])


def get_week_data(user_id: int, week_start: date, db: Session):
    days = [week_start + timedelta(days=i) for i in range(7)]
    return [compute_daily(user_id, d, db) for d in days]


@router.get("/weekly/csv")
def weekly_csv(
    week_start: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    summaries = get_week_data(current_user.id, week_start, db)

    output = StringIO()
    writer = csv.writer(output)

    # header
    writer.writerow([
        "Date", "Day",
        "Calories In", "Protein (g)", "Carbs (g)", "Fat (g)", "Fiber (g)",
        "TDEE", "BMR", "Walk Cals", "Gym Cals", "Deficit",
        "Weight (kg)", "Walk (km)", "Steps", "Water (ml)",
        "Gym Done", "Gym Mins", "Gym Intensity",
        "Sleep Hours", "Sleep Quality", "Mood",
        "Is Rest Day", "Is Fasting"
    ])

    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for i, s in enumerate(summaries):
        writer.writerow([
            s["date"], day_names[i],
            s.get("total_calories", 0),
            s.get("total_protein_g", 0),
            s.get("total_carbs_g", 0),
            s.get("total_fat_g", 0),
            s.get("total_fiber_g", 0),
            s.get("tdee") or "",
            s.get("bmr") or "",
            s.get("walk_cals") or "",
            s.get("gym_cals") or "",
            s.get("deficit") or "",
            s.get("weight_kg") or "",
            s.get("walk_km") or "",
            s.get("steps") or "",
            s.get("water_ml") or 0,
            s.get("gym_done") or False,
            s.get("gym_mins") or "",
            s.get("gym_intensity") or "",
            s.get("sleep_hours") or "",
            s.get("sleep_quality") or "",
            s.get("mood") or "",
            s.get("is_rest_day") or False,
            s.get("is_fasting") or False,
        ])

    output.seek(0)
    filename = f"health_report_{week_start}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/weekly/pdf")
def weekly_pdf(
    week_start: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    summaries = get_week_data(current_user.id, week_start, db)
    week_end = week_start + timedelta(days=6)
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm
    )

    styles = getSampleStyleSheet()
    accent = colors.HexColor("#1D9E75")
    dark = colors.HexColor("#1a1a18")
    light = colors.HexColor("#f5f4f0")
    muted = colors.HexColor("#6b6a66")

    h1 = ParagraphStyle("h1", fontSize=22, fontName="Helvetica-Bold",
                         textColor=dark, spaceAfter=4)
    h2 = ParagraphStyle("h2", fontSize=13, fontName="Helvetica-Bold",
                         textColor=dark, spaceAfter=6, spaceBefore=12)
    sub = ParagraphStyle("sub", fontSize=9, fontName="Helvetica",
                          textColor=muted, spaceAfter=12)
    note = ParagraphStyle("note", fontSize=8, fontName="Helvetica",
                           textColor=muted)

    def section(title):
        return [
            Spacer(1, 4*mm),
            HRFlowable(width="100%", thickness=0.5,
                       color=colors.HexColor("#e0ddd8")),
            Spacer(1, 2*mm),
            Paragraph(title, h2),
        ]

    def metric_table(rows, col_widths=None):
        t = Table(rows, colWidths=col_widths)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0ede8")),
            ("TEXTCOLOR", (0, 0), (-1, 0), muted),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#fafaf8")]),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e0ddd8")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        return t

    # compute week averages
    logged = [s for s in summaries if s["total_calories"] > 0]
    avg_cal = round(sum(s["total_calories"] for s in logged) / len(logged), 1) if logged else 0
    avg_tdee = round(sum(s["tdee"] for s in summaries if s.get("tdee")) /
                     max(len([s for s in summaries if s.get("tdee")]), 1), 1)
    avg_deficit = round(sum(s["deficit"] for s in summaries if s.get("deficit")) /
                        max(len([s for s in summaries if s.get("deficit")]), 1), 1)
    total_walk = round(sum(s.get("walk_km") or 0 for s in summaries), 1)
    avg_sleep = round(sum(s.get("sleep_hours") or 0 for s in summaries if s.get("sleep_hours")) /
                      max(len([s for s in summaries if s.get("sleep_hours")]), 1), 1) \
                if any(s.get("sleep_hours") for s in summaries) else None
    weights = [s["weight_kg"] for s in summaries if s.get("weight_kg")]
    weight_change = round(weights[-1] - weights[0], 2) if len(weights) >= 2 else None

    story = []

    # ── HEADER ──
    story.append(Paragraph("Weekly Health Report", h1))
    story.append(Paragraph(
        f"{current_user.name}  ·  "
        f"{week_start.strftime('%d %b')} — {week_end.strftime('%d %b %Y')}",
        sub
    ))

    # ── SUMMARY METRICS ──
    story += section("Week at a glance")
    summary_data = [
        ["Avg intake", "Avg TDEE", "Avg deficit", "Total walk", "Days logged"],
        [
            f"{avg_cal} kcal",
            f"{avg_tdee} kcal",
            f"{avg_deficit:+.0f} kcal" if avg_deficit else "—",
            f"{total_walk} km",
            f"{len(logged)}/7"
        ]
    ]
    if weight_change is not None:
        summary_data[0].append("Weight change")
        summary_data[1].append(f"{weight_change:+.2f} kg")
    story.append(metric_table(summary_data))

    if avg_sleep:
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph(f"Average sleep: {avg_sleep} hours", note))

    # ── DAILY NUTRITION ──
    story += section("Daily nutrition")
    nut_data = [["Day", "Date", "Calories", "Protein", "Carbs", "Fat", "Fiber", "Deficit"]]
    for i, s in enumerate(summaries):
        deficit_str = f"{s['deficit']:+.0f}" if s.get("deficit") else "—"
        nut_data.append([
            day_names[i], str(s["date"]),
            f"{int(s['total_calories'])}" if s["total_calories"] else "—",
            f"{s['total_protein_g']:.0f}g" if s["total_protein_g"] else "—",
            f"{s['total_carbs_g']:.0f}g" if s["total_carbs_g"] else "—",
            f"{s['total_fat_g']:.0f}g" if s["total_fat_g"] else "—",
            f"{s['total_fiber_g']:.0f}g" if s["total_fiber_g"] else "—",
            deficit_str,
        ])
    story.append(metric_table(nut_data))

    # ── DAILY ACTIVITY ──
    story += section("Daily activity")
    act_data = [["Day", "Weight", "Walk", "Walk kcal", "Gym", "Water", "Sleep", "Mood"]]
    for i, s in enumerate(summaries):
        act_data.append([
            day_names[i],
            f"{s['weight_kg']} kg" if s.get("weight_kg") else "—",
            f"{s['walk_km']} km" if s.get("walk_km") else "—",
            f"{int(s['walk_cals'])}" if s.get("walk_cals") else "—",
            f"{s['gym_mins']}min" if s.get("gym_done") and s.get("gym_mins") else
            ("Rest" if s.get("is_rest_day") else "—"),
            f"{int(s['water_ml'])} ml" if s.get("water_ml") else "—",
            f"{s['sleep_hours']}h" if s.get("sleep_hours") else "—",
            s.get("mood") or "—",
        ])
    story.append(metric_table(act_data))

    # ── WORKOUT SESSIONS ──
    sessions = db.query(WorkoutSession).filter(
        WorkoutSession.user_id == current_user.id,
        WorkoutSession.date >= week_start,
        WorkoutSession.date <= week_end
    ).order_by(WorkoutSession.date).all()

    if sessions:
        story += section("Workout sessions")
        for sess in sessions:
            sets = db.query(WorkoutSet).filter(
                WorkoutSet.session_id == sess.id
            ).all()
            sess_title = f"{sess.date.strftime('%a %d')}  —  {sess.name or 'Workout'}"
            if sess.is_rest_day:
                sess_title += "  (Rest day)"
            story.append(Paragraph(sess_title, ParagraphStyle(
                "sess", fontSize=10, fontName="Helvetica-Bold",
                textColor=accent, spaceBefore=8, spaceAfter=4
            )))
            if sess.duration_mins:
                story.append(Paragraph(
                    f"{sess.duration_mins} min  ·  {sess.intensity or ''}",
                    note
                ))
            if sets:
                by_ex = {}
                for s in sets:
                    ex = db.query(WorkoutExercise).filter(
                        WorkoutExercise.id == s.exercise_id
                    ).first()
                    name = ex.name if ex else f"Exercise #{s.exercise_id}"
                    if name not in by_ex:
                        by_ex[name] = []
                    by_ex[name].append(s)

                set_data = [["Exercise", "Set", "Reps", "Weight", "Duration"]]
                for ex_name, ex_sets in by_ex.items():
                    for s in ex_sets:
                        set_data.append([
                            ex_name if s.set_number == 1 else "",
                            str(s.set_number),
                            str(s.reps) if s.reps else "—",
                            f"{s.weight_kg} kg" if s.weight_kg else "—",
                            f"{s.duration_secs}s" if s.duration_secs else "—",
                        ])
                story.append(metric_table(set_data,
                    col_widths=[80, 25, 35, 45, 45]))
            story.append(Spacer(1, 2*mm))

    # ── FOOD LOG ──
    food_logs = db.query(FoodLog).filter(
        FoodLog.user_id == current_user.id,
        FoodLog.date >= week_start,
        FoodLog.date <= week_end
    ).order_by(FoodLog.date, FoodLog.meal_type).all()

    if food_logs:
        story += section("Food log")
        fl_data = [["Date", "Meal", "Food", "Qty", "Calories", "Protein", "Carbs", "Fat"]]
        for fl in food_logs:
            food = db.query(Food).filter(Food.id == fl.food_id).first()
            fl_data.append([
                str(fl.date),
                fl.meal_type,
                food.name if food else f"#{fl.food_id}",
                f"{fl.quantity}{fl.unit}",
                f"{fl.calories:.0f}",
                f"{fl.protein_g:.1f}g",
                f"{fl.carbs_g:.1f}g",
                f"{fl.fat_g:.1f}g",
            ])
        story.append(metric_table(fl_data,
            col_widths=[38, 35, 80, 28, 38, 38, 35, 35]))

    # ── FOOTER ──
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=colors.HexColor("#e0ddd8")))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        f"Generated by Health Tracker  ·  healthtracker.co.in  ·  {date.today()}",
        note
    ))

    doc.build(story)
    buffer.seek(0)
    filename = f"health_report_{week_start}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )