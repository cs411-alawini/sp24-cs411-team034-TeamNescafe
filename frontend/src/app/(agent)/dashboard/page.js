'use client';
import { useEffect, useState } from 'react';
import apiService from '@/controllers/apiService';
import Link from 'next/link';

export default function AgentDashboard() {
	const [dashboardData, setDashboardData] = useState([]);

	useEffect(() => {
		apiService.agentDashboard().then((data) => {
			setDashboardData(data);
		});
		console.log('Calling');
	}, []);

	return (
		<main className='flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-6'>
			<div className='flex items-center'>
				<h1 className='font-semibold text-lg md:text-2xl'>
					Applications per Unit
				</h1>
			</div>

			<div className='overflow-x-auto'>
				<table className='min-w-full'>
					<thead>
						<tr>
							<th className='px-4 py-2'>Unit No</th>
							<th className='px-4 py-2'>
								Property Name
							</th>
							<th className='px-4 py-2'>
								Number of Applications
							</th>
						</tr>
					</thead>
					<tbody>
						{dashboardData.map((item, index) => (
							<tr
								key={index}
								className={
									index % 2 === 0
										? 'bg-gray-100'
										: 'bg-white'
								}
							>
								<td className='border px-4 py-2 text-center underline underline-offset-4'>
									<Link
										href={`/unit/${item.unit_id}`}
									>
										{item.apartment_num}
									</Link>
								</td>
								<td className='border px-4 py-2 text-center'>
									<Link
										href={`/property_detail/${item.property_id}`}
									>
									{item.property_name}
									</Link>
								</td>
								<td className='border px-4 py-2 text-center'>
									{item.num_applications}
								</td>
							</tr>
						))}
					</tbody>
				</table>
			</div>
		</main>
	);
}
