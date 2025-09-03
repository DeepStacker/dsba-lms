"""Seed script to create sample Program, POs, Course, COs and CO->PO mappings"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.models import Program, PO, Course, CO, CO_PO_Map

async def seed():
    async with AsyncSessionLocal() as session:
        # Create program
        program = Program(name="BSc Computer Science", year=2025)
        session.add(program)
        await session.flush()

        # Create POs
        po1 = PO(program_id=program.id, code="PO1", title="Engineering knowledge", version=1)
        po2 = PO(program_id=program.id, code="PO2", title="Problem analysis", version=1)
        po3 = PO(program_id=program.id, code="PO3", title="Design/development", version=1)
        session.add_all([po1, po2, po3])
        await session.flush()

        # Create course
        course = Course(program_id=program.id, code="CS101", title="Intro to Programming", credits=3.0)
        session.add(course)
        await session.flush()

        # Create COs
        co1 = CO(course_id=course.id, code="CO1", title="Understand basics", bloom="Remember", version=1)
        co2 = CO(course_id=course.id, code="CO2", title="Apply programming", bloom="Apply", version=1)
        co3 = CO(course_id=course.id, code="CO3", title="Design solutions", bloom="Create", version=1)
        session.add_all([co1, co2, co3])
        await session.flush()

        # Create CO->PO mappings
        m1 = CO_PO_Map(co_id=co1.id, po_id=po1.id, weight=0.6)
        m2 = CO_PO_Map(co_id=co1.id, po_id=po2.id, weight=0.4)
        m3 = CO_PO_Map(co_id=co2.id, po_id=po2.id, weight=1.0)
        m4 = CO_PO_Map(co_id=co3.id, po_id=po3.id, weight=1.0)
        session.add_all([m1, m2, m3, m4])

        await session.commit()

if __name__ == '__main__':
    asyncio.run(seed())
